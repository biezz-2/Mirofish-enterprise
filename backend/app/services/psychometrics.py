"""
MiroFish Enterprise Whole Trait & Cybernetic Big Five Service (Agent 08: Divisi C)
Implementasi Whole Trait Theory (William Fleeson) dengan density distribution:
s = trait + noise (fluktuasi keadaan kepribadian di sekitar mean).
Dan Cybernetic Big Five Theory (Colin DeYoung) memetakan Big Five ke fungsi regulasi adaptif:
- O (Openness/Intellect): Eksplorasi kognitif dan persepsi
- C (Conscientiousness): Regulasi dan perlindungan target/tujuan
- E (Extraversion): Sensitivitas ganjaran (reward engagement)
- A (Agreeableness): Koordinasi sosial altruistik
- N (Neuroticism): Deteksi ancaman dan kecemasan
"""

import math
import random
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BigFiveTrait(BaseModel):
    """Representasi trait inti Big Five agen (mean baseline)."""
    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    conscientiousness: float = Field(default=0.5, ge=0.0, le=1.0)
    extraversion: float = Field(default=0.5, ge=0.0, le=1.0)
    agreeableness: float = Field(default=0.5, ge=0.0, le=1.0)
    neuroticism: float = Field(default=0.5, ge=0.0, le=1.0)


class SituationalPress(BaseModel):
    """
    Tekanan / stimulasi situasional lingkungan (Fleeson situational press).
    Menggeser densitas keadaan sementara agen berdasarkan stimulus eksternal.
    """
    threat: float = Field(default=0.0, ge=0.0, le=1.0, description="Tingkat ancaman / konflik / backlash")
    novelty: float = Field(default=0.0, ge=0.0, le=1.0, description="Tingkat kebaruan informasi / stimulasi kognitif")
    social: float = Field(default=0.0, ge=0.0, le=1.0, description="Kepadatan interaksi sosial / peluang afinitas")
    reward: float = Field(default=0.0, ge=0.0, le=1.0, description="Peluang reward / validasi / upvote / status")
    structure: float = Field(default=0.0, ge=0.0, le=1.0, description="Aturan platform / moderasi / tekanan kepatuhan")


class CyberneticAspects(BaseModel):
    """
    10 Sub-dimensi Aspek Cybernetic Big Five (DeYoung, Quilty, & Peterson, 2007).
    Memisahkan setiap dimensi Big Five menjadi dua aspek fungsional sibernetik.
    """
    # Openness / Intellect
    intellect: float = Field(default=0.5, ge=0.0, le=1.0, description="Eksplorasi kognitif, logika, rasa ingin tahu semantik")
    openness_to_experience: float = Field(default=0.5, ge=0.0, le=1.0, description="Eksplorasi persepsi, estetika, metafora")
    
    # Conscientiousness
    industriousness: float = Field(default=0.5, ge=0.0, le=1.0, description="Persistensi tujuan, perlindungan dari disrupsi")
    orderliness: float = Field(default=0.5, ge=0.0, le=1.0, description="Struktur, regulasi impuls, kepatuhan aturan")
    
    # Extraversion
    assertiveness: float = Field(default=0.5, ge=0.0, le=1.0, description="Reward wanting, inisiatif, dominasi sosial")
    enthusiasm: float = Field(default=0.5, ge=0.0, le=1.0, description="Reward liking, afeksi positif, kehangatan interaksi")
    
    # Agreeableness
    compassion: float = Field(default=0.5, ge=0.0, le=1.0, description="Empati, kepedulian terhadap kebutuhan agen lain")
    politeness: float = Field(default=0.5, ge=0.0, le=1.0, description="Penekanan agresi, kepatuhan kooperatif, rasa hormat")
    
    # Neuroticism
    volatility: float = Field(default=0.5, ge=0.0, le=1.0, description="Agresi defensif, iritabilitas, reaktivitas")
    withdrawal: float = Field(default=0.5, ge=0.0, le=1.0, description="Kecemasan, sensor diri, penghindaran ancaman")


class PersonalityState(BaseModel):
    """Keadaan kepribadian momen tertentu (state) beserta dorongan sibernetik adaptif."""
    state_openness: float
    state_conscientiousness: float
    state_extraversion: float
    state_agreeableness: float
    state_neuroticism: float
    exploration_drive: float
    goal_persistence: float
    reward_sensitivity: float
    social_trust: float
    threat_sensitivity: float

    # Metatraits & Aspek Sibernetik Tambahan (DeYoung 2006, 2015)
    stability: float = Field(default=0.5, description="Metatrait Stabilitas: (C + A + (1-N)) / 3")
    plasticity: float = Field(default=0.5, description="Metatrait Plastisitas: (E + O) / 2")
    aspects: Optional[CyberneticAspects] = None
    situational_modulation: Optional[Dict[str, float]] = None
    homeostasis_deviation: float = Field(default=0.0, description="Deviasi kuadrat rata-rata terhadap baseline trait")


class AnomalyReport(BaseModel):
    """Laporan anomali perilaku atau degradasi stabilitas dalam simulasi."""
    round_num: int
    anomaly_type: str  # 'boundary_saturation', 'oscillatory_instability', 'identity_drift', 'cybernetic_freezing'
    trait_name: str
    value: float
    threshold: float
    description: str


class TrajectoryResult(BaseModel):
    """Hasil simulasi lintasan keadaan dinamis agen sepanjang sejumlah ronde."""
    agent_id: str
    baseline_trait: BigFiveTrait
    rounds: int
    states: List[PersonalityState]
    mean_states: Dict[str, float]
    variance_states: Dict[str, float]
    max_deviations: Dict[str, float]
    identity_preserved: bool
    stability_score: float
    anomalies: List[AnomalyReport] = Field(default_factory=list)


class DownstreamRecommendation(BaseModel):
    """Rekomendasi parameter terkalibrasi untuk downstream Agent 09 (ODE) dan Agent 10 (Decision)."""
    agent_id: Optional[str] = None
    agent_09_needs: Dict[str, Any]
    agent_10_decision: Dict[str, Any]
    cybernetic_summary: Dict[str, float]


class SwarmSimulationResult(BaseModel):
    """Hasil evaluasi simulasi swarm multi-agent sandbox."""
    population_size: int
    rounds: int
    convergence_rate: float
    identity_retention_rate: float
    deadlock_detected: bool
    deadlock_details: List[str] = Field(default_factory=list)
    mean_population_stability: float
    mean_population_plasticity: float
    collective_entropy: float
    homeostasis_recovery_rounds: int
    agent_summaries: List[Dict[str, Any]] = Field(default_factory=list)


class PsychometricsEngine:
    """
    Simulates Fleeson Whole Trait density distribution & DeYoung Cybernetics.
    
    Mendukung:
    1. Densitas keadaan momen Fleeson: s = baseline + situational_press + Gaussian noise.
    2. Inersia keadaan temporal autoregresif AR(1): s_t = alpha * s_{t-1} + (1-alpha) * s_target.
    3. Pemetaan Cybernetic Big Five DeYoung: 10 aspek dan dorongan perilaku fungsional.
    4. Evaluasi stabilitas konvergensi dan preservasi identitas inti agen.
    5. Deteksi anomali (deadlock pembekuan sibernetik, saturasi batas, drift identitas).
    6. Rekomendasi parameter kuantitatif untuk downstream Agent 09 & Agent 10.
    """

    def __init__(
        self,
        sigma_noise: float = 0.08,
        state_inertia: float = 0.35,
        default_tolerance: float = 0.10,
        random_seed: Optional[int] = None
    ):
        self.sigma_noise = sigma_noise
        self.state_inertia = state_inertia
        self.default_tolerance = default_tolerance
        if random_seed is not None:
            random.seed(random_seed)

    def _compute_situational_deltas(self, press: Optional[SituationalPress]) -> Dict[str, float]:
        """
        Menghitung pergeseran mean keadaan akibat tekanan lingkungan situasional.
        Fleeson & Jayawickreme (2015): situasi menyediakan affordance untuk aktivasi keadaan.
        """
        if press is None:
            return {"o": 0.0, "c": 0.0, "e": 0.0, "a": 0.0, "n": 0.0}

        # Formulasi pergeseran sibernetik
        delta_o = 0.15 * press.novelty + 0.05 * press.reward - 0.08 * press.threat
        delta_c = 0.15 * press.structure - 0.08 * press.threat
        delta_e = 0.18 * press.reward + 0.12 * press.social - 0.10 * press.threat
        delta_a = 0.15 * press.social - 0.20 * press.threat
        delta_n = 0.25 * press.threat - 0.10 * press.social - 0.05 * press.reward

        return {
            "o": delta_o,
            "c": delta_c,
            "e": delta_e,
            "a": delta_a,
            "n": delta_n
        }

    def compute_aspects(
        self,
        s_o: float,
        s_c: float,
        s_e: float,
        s_a: float,
        s_n: float
    ) -> CyberneticAspects:
        """
        Menghitung 10 sub-dimensi aspek Cybernetic Big Five DeYoung (2007, 2014).
        """
        def clamp(v: float) -> float:
            return round(max(0.0, min(1.0, v)), 3)

        intellect = clamp(s_o * 1.05 + 0.05 * s_c)
        openness_exp = clamp(s_o * 0.95 + 0.05 * s_e)

        industriousness = clamp(s_c * 1.10 - 0.10 * s_n)
        orderliness = clamp(s_c * 0.95 + 0.05 * (1.0 - s_o))

        assertiveness = clamp(s_e * 1.10 + 0.05 * (1.0 - s_n))
        enthusiasm = clamp(s_e * 0.95 + 0.10 * s_a)

        compassion = clamp(s_a * 1.05 + 0.05 * s_o)
        politeness = clamp(s_a * 0.95 + 0.10 * s_c - 0.05 * s_n)

        volatility = clamp(s_n * 1.10 - 0.10 * s_a)
        withdrawal = clamp(s_n * 1.05 - 0.10 * s_e)

        return CyberneticAspects(
            intellect=intellect,
            openness_to_experience=openness_exp,
            industriousness=industriousness,
            orderliness=orderliness,
            assertiveness=assertiveness,
            enthusiasm=enthusiasm,
            compassion=compassion,
            politeness=politeness,
            volatility=volatility,
            withdrawal=withdrawal
        )

    def sample_state(
        self,
        trait: BigFiveTrait,
        press: Optional[SituationalPress] = None,
        previous_state: Optional[PersonalityState] = None
    ) -> PersonalityState:
        """
        Menerapkan Whole Trait Fleeson: s = mean + situational_deltas + Gaussian noise,
        dengan inersia autoregresif jika previous_state diberikan.
        Dibatasi ketat dalam rentang [0.0, 1.0].
        """
        deltas = self._compute_situational_deltas(press)

        def sample_var(val: float, delta: float, prev_val: Optional[float] = None) -> float:
            noise = random.gauss(0.0, self.sigma_noise)
            target = max(0.0, min(1.0, val + delta + noise))
            if prev_val is not None:
                combined = (self.state_inertia * prev_val) + ((1.0 - self.state_inertia) * target)
                return max(0.0, min(1.0, combined))
            return target

        prev_o = previous_state.state_openness if previous_state else None
        prev_c = previous_state.state_conscientiousness if previous_state else None
        prev_e = previous_state.state_extraversion if previous_state else None
        prev_a = previous_state.state_agreeableness if previous_state else None
        prev_n = previous_state.state_neuroticism if previous_state else None

        s_o = sample_var(trait.openness, deltas["o"], prev_o)
        s_c = sample_var(trait.conscientiousness, deltas["c"], prev_c)
        s_e = sample_var(trait.extraversion, deltas["e"], prev_e)
        s_a = sample_var(trait.agreeableness, deltas["a"], prev_a)
        s_n = sample_var(trait.neuroticism, deltas["n"], prev_n)

        # DeYoung Cybernetic Function Mapping (kompatibilitas backward penuh)
        exploration_drive = round(s_o * 1.2, 3)
        goal_persistence = round(s_c * 1.1, 3)
        reward_sensitivity = round(s_e * 1.3, 3)
        social_trust = round(s_a * 1.0, 3)
        threat_sensitivity = round(s_n * 1.4, 3)

        # Metatraits (DeYoung 2006)
        stability = round((s_c + s_a + (1.0 - s_n)) / 3.0, 3)
        plasticity = round((s_e + s_o) / 2.0, 3)

        aspects = self.compute_aspects(s_o, s_c, s_e, s_a, s_n)

        # Deviasi homeostasis terhadap baseline
        deviation = math.sqrt(
            ((s_o - trait.openness) ** 2 +
             (s_c - trait.conscientiousness) ** 2 +
             (s_e - trait.extraversion) ** 2 +
             (s_a - trait.agreeableness) ** 2 +
             (s_n - trait.neuroticism) ** 2) / 5.0
        )

        return PersonalityState(
            state_openness=round(s_o, 4),
            state_conscientiousness=round(s_c, 4),
            state_extraversion=round(s_e, 4),
            state_agreeableness=round(s_a, 4),
            state_neuroticism=round(s_n, 4),
            exploration_drive=exploration_drive,
            goal_persistence=goal_persistence,
            reward_sensitivity=reward_sensitivity,
            social_trust=social_trust,
            threat_sensitivity=threat_sensitivity,
            stability=stability,
            plasticity=plasticity,
            aspects=aspects,
            situational_modulation=deltas,
            homeostasis_deviation=round(deviation, 4)
        )

    def sample_distribution(self, trait: BigFiveTrait, n_samples: int = 1000) -> Dict[str, Any]:
        """
        Uji stabilitas statistik density distribution Fleeson across all Big Five dimensions.
        Mempertahankan format dict output eksisting untuk kompatibilitas uji v32.
        """
        samples = [self.sample_state(trait) for _ in range(n_samples)]
        
        o_vals = [s.state_openness for s in samples]
        c_vals = [s.state_conscientiousness for s in samples]
        e_vals = [s.state_extraversion for s in samples]
        a_vals = [s.state_agreeableness for s in samples]
        n_vals = [s.state_neuroticism for s in samples]

        mean_o = sum(o_vals) / n_samples
        mean_c = sum(c_vals) / n_samples
        mean_e = sum(e_vals) / n_samples
        mean_a = sum(a_vals) / n_samples
        mean_n = sum(n_vals) / n_samples

        std_o = math.sqrt(sum((v - mean_o) ** 2 for v in o_vals) / n_samples)
        diff_o = abs(mean_o - trait.openness)

        is_stable_all = (
            abs(mean_o - trait.openness) < self.default_tolerance and
            abs(mean_c - trait.conscientiousness) < self.default_tolerance and
            abs(mean_e - trait.extraversion) < self.default_tolerance and
            abs(mean_a - trait.agreeableness) < self.default_tolerance and
            abs(mean_n - trait.neuroticism) < self.default_tolerance
        )

        return {
            "mean": mean_o,
            "expected": trait.openness,
            "deviation": diff_o,
            "is_stable": diff_o < self.default_tolerance,
            "std_dev": round(std_o, 4),
            "all_traits_stable": is_stable_all,
            "all_traits": {
                "openness": {"mean": round(mean_o, 4), "expected": trait.openness, "deviation": round(diff_o, 4)},
                "conscientiousness": {"mean": round(mean_c, 4), "expected": trait.conscientiousness, "deviation": round(abs(mean_c - trait.conscientiousness), 4)},
                "extraversion": {"mean": round(mean_e, 4), "expected": trait.extraversion, "deviation": round(abs(mean_e - trait.extraversion), 4)},
                "agreeableness": {"mean": round(mean_a, 4), "expected": trait.agreeableness, "deviation": round(abs(mean_a - trait.agreeableness), 4)},
                "neuroticism": {"mean": round(mean_n, 4), "expected": trait.neuroticism, "deviation": round(abs(mean_n - trait.neuroticism), 4)},
            }
        }

    def simulate_trajectory(
        self,
        trait: BigFiveTrait,
        n_rounds: int = 50,
        press_sequence: Optional[List[SituationalPress]] = None,
        agent_id: str = "agent-001"
    ) -> TrajectoryResult:
        """
        Simulasi lintasan dinamis satu agen sepanjang n_rounds.
        Memverifikasi Whole Trait Theory:
        1. Adanya variansi keadaan (s tidak statis).
        2. Retensi identitas inti: rata-rata jangka panjang konvergen ke trait baseline.
        """
        states: List[PersonalityState] = []
        current_state: Optional[PersonalityState] = None

        for r in range(n_rounds):
            press = press_sequence[r] if (press_sequence and r < len(press_sequence)) else None
            current_state = self.sample_state(trait, press=press, previous_state=current_state)
            states.append(current_state)

        o_vals = [s.state_openness for s in states]
        c_vals = [s.state_conscientiousness for s in states]
        e_vals = [s.state_extraversion for s in states]
        a_vals = [s.state_agreeableness for s in states]
        n_vals = [s.state_neuroticism for s in states]

        mean_states = {
            "openness": round(sum(o_vals) / n_rounds, 4),
            "conscientiousness": round(sum(c_vals) / n_rounds, 4),
            "extraversion": round(sum(e_vals) / n_rounds, 4),
            "agreeableness": round(sum(a_vals) / n_rounds, 4),
            "neuroticism": round(sum(n_vals) / n_rounds, 4),
        }

        variance_states = {
            "openness": round(sum((v - mean_states["openness"]) ** 2 for v in o_vals) / n_rounds, 5),
            "conscientiousness": round(sum((v - mean_states["conscientiousness"]) ** 2 for v in c_vals) / n_rounds, 5),
            "extraversion": round(sum((v - mean_states["extraversion"]) ** 2 for v in e_vals) / n_rounds, 5),
            "agreeableness": round(sum((v - mean_states["agreeableness"]) ** 2 for v in a_vals) / n_rounds, 5),
            "neuroticism": round(sum((v - mean_states["neuroticism"]) ** 2 for v in n_vals) / n_rounds, 5),
        }

        max_deviations = {
            "openness": round(abs(mean_states["openness"] - trait.openness), 4),
            "conscientiousness": round(abs(mean_states["conscientiousness"] - trait.conscientiousness), 4),
            "extraversion": round(abs(mean_states["extraversion"] - trait.extraversion), 4),
            "agreeableness": round(abs(mean_states["agreeableness"] - trait.agreeableness), 4),
            "neuroticism": round(abs(mean_states["neuroticism"] - trait.neuroticism), 4),
        }

        # Preservasi identitas: jika tidak ada press sepihak yang ekstrim, mean harus dekat dengan baseline
        max_dev = max(max_deviations.values())
        identity_preserved = max_dev <= (self.default_tolerance + 0.05)
        stability_score = round(max(0.0, 1.0 - max_dev), 3)

        # Deteksi anomali pada trajectory
        anomalies: List[AnomalyReport] = []
        for idx, s in enumerate(states):
            # 1. Boundary saturation check (0.0 atau 1.0)
            for trait_name, val in [
                ("openness", s.state_openness),
                ("conscientiousness", s.state_conscientiousness),
                ("extraversion", s.state_extraversion),
                ("agreeableness", s.state_agreeableness),
                ("neuroticism", s.state_neuroticism),
            ]:
                if val <= 0.001 or val >= 0.999:
                    anomalies.append(AnomalyReport(
                        round_num=idx + 1,
                        anomaly_type="boundary_saturation",
                        trait_name=trait_name,
                        value=val,
                        threshold=0.001 if val <= 0.001 else 0.999,
                        description=f"Saturasi batas ekstrim terdeteksi pada {trait_name}: {val}"
                    ))
            
            # 2. Oscillatory instability check (|s_t - s_{t-1}| > 0.45)
            if idx > 0:
                prev = states[idx - 1]
                for trait_name, cur_v, prev_v in [
                    ("openness", s.state_openness, prev.state_openness),
                    ("neuroticism", s.state_neuroticism, prev.state_neuroticism),
                    ("extraversion", s.state_extraversion, prev.state_extraversion),
                ]:
                    jump = abs(cur_v - prev_v)
                    if jump > 0.45:
                        anomalies.append(AnomalyReport(
                            round_num=idx + 1,
                            anomaly_type="oscillatory_instability",
                            trait_name=trait_name,
                            value=jump,
                            threshold=0.45,
                            description=f"Lompatan osilasi liar terdeteksi pada {trait_name}: Delta={round(jump, 3)}"
                        ))

        return TrajectoryResult(
            agent_id=agent_id,
            baseline_trait=trait,
            rounds=n_rounds,
            states=states,
            mean_states=mean_states,
            variance_states=variance_states,
            max_deviations=max_deviations,
            identity_preserved=identity_preserved,
            stability_score=stability_score,
            anomalies=anomalies
        )

    def simulate_swarm_population(
        self,
        traits: List[BigFiveTrait],
        n_rounds: int = 20,
        press_sequence: Optional[List[SituationalPress]] = None,
        shock_round: Optional[int] = None,
        shock_press: Optional[SituationalPress] = None
    ) -> SwarmSimulationResult:
        """
        Simulasi sandbox populasi agen swarm multi-round untuk evaluasi:
        1. Stabilitas konvergensi kolektif.
        2. Retensi identitas inti seluruh agen.
        3. Deteksi potensi deadlock (mis. cybernetic freezing saat ancaman ekstrem).
        4. Durasi pemulihan homeostasis pasca-shock ancaman/stres.
        """
        n_agents = len(traits)
        if n_agents == 0:
            raise ValueError("Populasi traits tidak boleh kosong.")

        trajectories: List[TrajectoryResult] = []
        for idx, tr in enumerate(traits):
            agent_press_seq: List[SituationalPress] = []
            for r in range(n_rounds):
                if shock_round is not None and r == shock_round and shock_press is not None:
                    agent_press_seq.append(shock_press)
                elif press_sequence and r < len(press_sequence):
                    agent_press_seq.append(press_sequence[r])
                else:
                    agent_press_seq.append(SituationalPress())

            traj = self.simulate_trajectory(
                trait=tr,
                n_rounds=n_rounds,
                press_sequence=agent_press_seq,
                agent_id=f"agent-{idx:03d}"
            )
            trajectories.append(traj)

        # Evaluasi metrik kolektif
        preserved_count = sum(1 for t in trajectories if t.identity_preserved)
        identity_retention_rate = round(preserved_count / n_agents, 4)

        all_deviations = [max(t.max_deviations.values()) for t in trajectories]
        avg_deviation = sum(all_deviations) / n_agents
        convergence_rate = round(max(0.0, 1.0 - avg_deviation), 4)

        # Deteksi Deadlock (Cybernetic Freezing)
        # Jika rata-rata threat_sensitivity populasi > 0.85 dan reward_sensitivity < 0.20
        deadlock_detected = False
        deadlock_details: List[str] = []

        for r in range(n_rounds):
            round_threats = [t.states[r].threat_sensitivity for t in trajectories]
            round_rewards = [t.states[r].reward_sensitivity for t in trajectories]
            avg_threat = sum(round_threats) / n_agents
            avg_reward = sum(round_rewards) / n_agents

            if avg_threat > 0.85 and avg_reward < 0.20:
                deadlock_detected = True
                deadlock_details.append(
                    f"Ronde {r + 1}: Cybernetic Freezing terdeteksi! Rata-rata threat_sensitivity={round(avg_threat, 3)} melebihi 0.85 dengan reward_sensitivity={round(avg_reward, 3)} < 0.20"
                )

        # Metatraits populasi
        last_states = [t.states[-1] for t in trajectories]
        mean_stability = round(sum(s.stability for s in last_states) / n_agents, 4)
        mean_plasticity = round(sum(s.plasticity for s in last_states) / n_agents, 4)

        # Shannon Entropy dari distribusi orientasi Plastisitas/Stabilitas
        bins = [0] * 5
        for s in last_states:
            bin_idx = min(4, int(s.stability * 5))
            bins[bin_idx] += 1
        entropy = 0.0
        for b in bins:
            if b > 0:
                p = b / n_agents
                entropy -= p * math.log2(p)

        # Durasi pemulihan homeostasis pasca-shock
        recovery_rounds = 0
        if shock_round is not None and shock_round < n_rounds:
            baseline_avg_dev = sum(t.states[shock_round - 1].homeostasis_deviation for t in trajectories) / n_agents if shock_round > 0 else 0.05
            for r in range(shock_round + 1, n_rounds):
                current_avg_dev = sum(t.states[r].homeostasis_deviation for t in trajectories) / n_agents
                if current_avg_dev <= baseline_avg_dev * 1.25:
                    recovery_rounds = r - shock_round
                    break
            if recovery_rounds == 0 and n_rounds > shock_round:
                recovery_rounds = n_rounds - shock_round

        agent_summaries = [
            {
                "agent_id": t.agent_id,
                "stability_score": t.stability_score,
                "identity_preserved": t.identity_preserved,
                "anomalies_count": len(t.anomalies)
            }
            for t in trajectories[:10]  # Ringkasan 10 agen pertama untuk payload hemat ruang
        ]

        return SwarmSimulationResult(
            population_size=n_agents,
            rounds=n_rounds,
            convergence_rate=convergence_rate,
            identity_retention_rate=identity_retention_rate,
            deadlock_detected=deadlock_detected,
            deadlock_details=deadlock_details,
            mean_population_stability=mean_stability,
            mean_population_plasticity=mean_plasticity,
            collective_entropy=round(entropy, 4),
            homeostasis_recovery_rounds=recovery_rounds,
            agent_summaries=agent_summaries
        )

    def get_downstream_recommendation(
        self,
        state: PersonalityState,
        agent_id: Optional[str] = None
    ) -> DownstreamRecommendation:
        """
        Menyediakan pemetaan parameter sibernetik terkalibrasi untuk downstream
        Agent 09 (Humanoid Needs ODE) dan Agent 10 (Nested Logit & DDM).
        """
        aspects = state.aspects or self.compute_aspects(
            state.state_openness,
            state.state_conscientiousness,
            state.state_extraversion,
            state.state_agreeableness,
            state.state_neuroticism
        )

        # 1. Kalibrasi untuk Agent 09 (Humanoid ODE Needs)
        # - Peluruhan energi lebih cepat pada neurotisisme tinggi (stres) dan lebih lambat pada kegigihan tinggi
        base_lambda_energy = 0.05
        lambda_energy_eff = round(base_lambda_energy * (1.0 + 0.35 * state.threat_sensitivity - 0.20 * state.goal_persistence), 4)

        # - Peluruhan dorongan sosial lebih cepat pada ekstraversi tinggi (cepat bosan/haus interaksi)
        base_lambda_social = 0.03
        lambda_social_eff = round(base_lambda_social * (1.0 + 0.40 * state.reward_sensitivity), 4)

        # - Emosi dasar Ekman Paul Ekman (7 emosi)
        ekman = {
            "joy": round(max(0.0, min(1.0, 0.50 * state.state_extraversion + 0.30 * (1.0 - state.state_neuroticism))), 3),
            "sadness": round(max(0.0, min(1.0, 0.60 * aspects.withdrawal + 0.40 * (1.0 - state.state_extraversion))), 3),
            "anger": round(max(0.0, min(1.0, 0.70 * aspects.volatility + 0.30 * (1.0 - state.state_agreeableness))), 3),
            "fear": round(max(0.0, min(1.0, 0.75 * aspects.withdrawal + 0.25 * state.threat_sensitivity)), 3),
            "disgust": round(max(0.0, min(1.0, 0.50 * (1.0 - state.state_openness) + 0.50 * (1.0 - state.state_agreeableness))), 3),
            "surprise": round(max(0.0, min(1.0, 0.60 * state.state_openness + 0.40 * aspects.intellect)), 3),
            "trust": round(max(0.0, min(1.0, 0.70 * state.state_agreeableness + 0.30 * state.social_trust)), 3),
        }

        # 2. Kalibrasi untuk Agent 10 (Nested Logit & DDM)
        # - Utilitas lurker ditingkatkan oleh kecemasan penarikan diri (withdrawal)
        adj_utility_lurker = round(0.50 + 0.60 * aspects.withdrawal - 0.40 * state.reward_sensitivity, 3)

        # - Drift rate DDM ditingkatkan oleh exploration drive dan diturunkan oleh ancaman
        ddm_drift = round(max(0.05, 0.30 * (0.6 + 0.4 * state.exploration_drive) - 0.15 * state.threat_sensitivity), 3)

        # - Loss aversion lambda Prospect Theory dinaikkan oleh sensitivitas ancaman
        prospect_lambda = round(2.25 * (1.0 + 0.40 * state.threat_sensitivity - 0.20 * state.reward_sensitivity), 3)

        return DownstreamRecommendation(
            agent_id=agent_id,
            agent_09_needs={
                "effective_lambda_energy": lambda_energy_eff,
                "effective_lambda_social": lambda_social_eff,
                "baseline_ekman_emotions": ekman,
                "circadian_sleep_resilience": round(0.5 + 0.5 * aspects.orderliness, 3)
            },
            agent_10_decision={
                "adjusted_utility_lurker": adj_utility_lurker,
                "ddm_drift_rate": ddm_drift,
                "prospect_lambda_loss": prospect_lambda,
                "risk_tolerance": round(max(0.1, 1.0 - 0.7 * state.threat_sensitivity), 3)
            },
            cybernetic_summary={
                "stability": state.stability,
                "plasticity": state.plasticity,
                "exploration_drive": state.exploration_drive,
                "threat_sensitivity": state.threat_sensitivity,
                "reward_sensitivity": state.reward_sensitivity
            }
        )

    def generate_archetype_population(
        self,
        n_agents: int = 100,
        custom_ratios: Optional[Dict[str, float]] = None
    ) -> List[BigFiveTrait]:
        """
        Menghasilkan populasi BigFiveTrait agen berskala besar berdasarkan arketipe sosial
        yang realistis untuk platform simulasi (Step 2 Multi-Agent Simulation).
        """
        ratios = custom_ratios or {
            "lurker": 0.50,
            "analyst": 0.15,
            "influencer": 0.10,
            "mediator": 0.15,
            "critic": 0.10
        }

        archetypes = {
            "lurker": BigFiveTrait(openness=0.35, conscientiousness=0.50, extraversion=0.20, agreeableness=0.55, neuroticism=0.45),
            "analyst": BigFiveTrait(openness=0.85, conscientiousness=0.80, extraversion=0.45, agreeableness=0.40, neuroticism=0.30),
            "influencer": BigFiveTrait(openness=0.75, conscientiousness=0.60, extraversion=0.85, agreeableness=0.65, neuroticism=0.25),
            "mediator": BigFiveTrait(openness=0.60, conscientiousness=0.65, extraversion=0.60, agreeableness=0.85, neuroticism=0.20),
            "critic": BigFiveTrait(openness=0.50, conscientiousness=0.40, extraversion=0.65, agreeableness=0.20, neuroticism=0.75),
        }

        population: List[BigFiveTrait] = []
        for arch_name, ratio in ratios.items():
            count = int(round(n_agents * ratio))
            base = archetypes.get(arch_name, archetypes["lurker"])
            for _ in range(count):
                # Variasi Gaussian kecil (+/- 0.04) di sekitar mean arketipe
                def perturb(v: float) -> float:
                    return round(max(0.05, min(0.95, v + random.gauss(0.0, 0.04))), 3)

                population.append(BigFiveTrait(
                    openness=perturb(base.openness),
                    conscientiousness=perturb(base.conscientiousness),
                    extraversion=perturb(base.extraversion),
                    agreeableness=perturb(base.agreeableness),
                    neuroticism=perturb(base.neuroticism)
                ))

        # Pad or trim to exact n_agents
        while len(population) < n_agents:
            population.append(archetypes["lurker"])
        return population[:n_agents]
