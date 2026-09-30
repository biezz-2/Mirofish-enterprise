# backend/app/services/multi_platform_simulator.py
"""
Koordinator simulasi multi-platform: menjalankan satu PlatformSimulator
per platform aktif secara paralel, dengan checkpoint per ronde.
"""
import os, pickle, hashlib, threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
from .platform_behaviors import (
    PLATFORM_CHARACTERISTICS, DEFAULT_PLATFORMS,
    get_platform_behavior, compute_feed_score, is_viral,
)

class PlatformSimulator:
    """Satu sesi simulasi untuk satu platform."""

    def __init__(self, platform: str, agents: List[dict], config: dict,
                 snapshot_dir: str, llm_client=None):
        self.platform = platform
        self.behavior = get_platform_behavior(platform)
        self.characteristics = PLATFORM_CHARACTERISTICS[platform]
        self.agents = agents
        self.config = config
        self.posts: List[dict] = []
        self.round = 0
        self.llm = llm_client
        self.snapshot_dir = os.path.join(snapshot_dir, platform)
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self.degraded = False

    def run_round(self):
        """Satu ronde: aktivitas agen -> feed -> aksi -> metrik."""
        for agent in self._active_agents():
            feed = self._build_feed(agent)
            if not feed:
                action = self._choose_action(agent)
                if action == "post" or len(self.posts) == 0:
                    content = self._generate_content(agent)
                    if len(content) > self.characteristics["max_content_length"]:
                        content = content[: self.characteristics["max_content_length"]]
                    self.posts.append({
                        "id": len(self.posts),
                        "author": agent["id"],
                        "content": content,
                        "engagement": 0,
                        "mean_opinion": agent.get("opinion_score", 0.0),
                        "age_hours": 0
                    })
            for post in feed[: self.config.get("feed_size", 10)]:
                action = self._choose_action(agent)
                if action == "post":
                    content = self._generate_content(agent)
                    if len(content) > self.characteristics["max_content_length"]:
                        content = content[: self.characteristics["max_content_length"]]
                    self.posts.append({
                        "id": len(self.posts),
                        "author": agent["id"],
                        "content": content,
                        "engagement": 0,
                        "mean_opinion": agent.get("opinion_score", 0.0),
                        "age_hours": 0
                    })
                else:
                    post["engagement"] = post.get("engagement", 0) + (1 if action in ("like", "upvote") else 2)
                    agent["opinion_score"] = max(-1.0, min(1.0,
                        agent.get("opinion_score", 0.0) + 0.05 * (post["mean_opinion"] - agent.get("opinion_score", 0.0))))
        for p in self.posts:
            p["age_hours"] += self.config.get("round_minutes", 30) / 60.0
            if is_viral(self.platform, p):
                p["viral"] = True
        self.round += 1
        self._checkpoint()

    def _active_agents(self):
        return [a for a in self.agents if a.get("activity_level", 0.5) > 0.2]

    def _build_feed(self, agent) -> List[dict]:
        hour = self.config.get("current_hour", 12)
        scored = [(compute_feed_score(self.platform, p, agent, hour), p) for p in self.posts]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored]

    def _choose_action(self, agent) -> str:
        probs = self.behavior.action_probabilities
        import random
        r = random.random()
        acc = 0.0
        for action, p in probs.items():
            acc += p
            if r <= acc:
                return action
        return "like"

    def _generate_content(self, agent) -> str:
        if self.llm is None:
            name = agent.get("persona", {}).get("name", "Agen")
            return f"[{name}] menulis postingan di {self.platform}"
        prompt = (f"Kamu adalah {agent.get('persona', {}).get('name', 'Agen')}. {agent.get('persona', {}).get('bio', '')}. "
                  f"Tulis postingan media sosial ({self.behavior.content_style}) "
                  f"dalam Bahasa Indonesia, maksimal {self.characteristics['max_content_length']} karakter.")
        return self.llm.chat(prompt)

    def _checkpoint(self):
        """Snapshot ronde + hash (dasar pemulihan)."""
        path = os.path.join(self.snapshot_dir, f"round_{self.round:04d}.pkl")
        data = {"round": self.round, "agents": self.agents, "posts": self.posts}
        with open(path, "wb") as f:
            blob = pickle.dumps(data)
            f.write(blob)
        digest = hashlib.sha256(blob).hexdigest()
        with open(path + ".sha256", "w") as f:
            f.write(digest)

    def restore(self, round_no: int):
        path = os.path.join(self.snapshot_dir, f"round_{round_no:04d}.pkl")
        expected = open(path + ".sha256").read().strip()
        with open(path, "rb") as f:
            blob = f.read()
        assert hashlib.sha256(blob).hexdigest() == expected, "Checksum snapshot tidak cocok"
        data = pickle.loads(blob)
        self.round, self.agents, self.posts = data["round"], data["agents"], data["posts"]


class MultiPlatformSimulator:
    """Koordinator lintas platform paralel."""

    def __init__(self, enabled_platforms: List[str], agents_by_platform: Dict[str, List[dict]],
                 config: dict, workdir: str = "./snapshots", llm_client=None):
        self.config = config
        job_id = config.get("job_id", "job")
        self.simulators = {
            p: PlatformSimulator(p, agents_by_platform.get(p, []), config,
                                 snapshot_dir=os.path.join(workdir, job_id),
                                 llm_client=llm_client)
            for p in enabled_platforms
        }
        self.results: Dict[str, dict] = {}

    def run(self, rounds: int, checkpoint_every: int = 1):
        for r in range(1, rounds + 1):
            with ThreadPoolExecutor(max_workers=max(len(self.simulators), 1)) as ex:
                futures = {p: ex.submit(sim.run_round) for p, sim in self.simulators.items()}
                for p, fut in futures.items():
                    try:
                        fut.result(timeout=self.config.get("round_timeout_s", 3600))
                    except Exception as e:
                        self.simulators[p].degraded = True
                        print(f"[MultiPlatform] platform {p} degraded: {e}")
            if r % checkpoint_every == 0:
                print(f"[MultiPlatform] ronde {r} selesai (checkpoint tertulis)")
        return self.aggregate_results()

    def aggregate_results(self) -> dict:
        """Laporan lintas platform berbobot populasi."""
        total_pop = sum(len(s.agents) for s in self.simulators.values()) or 1
        agg = {"platforms": {}, "mean_opinion": 0.0, "viral_posts": 0}
        for p, s in self.simulators.items():
            opinion = sum(a.get("opinion_score", 0.0) for a in s.agents) / max(len(s.agents), 1)
            agg["platforms"][p] = {
                "round": s.round,
                "degraded": s.degraded,
                "mean_opinion": round(opinion, 3),
                "posts": len(s.posts),
                "viral": sum(1 for x in s.posts if x.get("viral")),
            }
            agg["mean_opinion"] += opinion * (len(s.agents) / total_pop)
            agg["viral_posts"] += agg["platforms"][p]["viral"]
        agg["mean_opinion"] = round(agg["mean_opinion"], 3)
        return agg

    def recover(self, last_rounds: Dict[str, int]):
        """Pemulihan per platform dari checkpoint terakhir masing-masing."""
        for p, r in last_rounds.items():
            if p in self.simulators:
                self.simulators[p].restore(r)
