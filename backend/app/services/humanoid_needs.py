"""
MiroFish Enterprise Humanoid ODE & Ekman Needs Engine (Agent 09: Divisi C)
Model System 1 Humanoid:
- ODE Peluruhan Kebutuhan: dN/dt = -lambda * N + R(t) (energi, sosialisasi, stimulasi, pencapaian)
- 7 Emosi Dasar Paul Ekman: Joy, Sadness, Anger, Fear, Disgust, Surprise, Trust
- Pemetaan Sirkumpleks Russell: Valensi (-1 s.d. 1), Arousal (0 s.d. 1), Dominansi (-1 s.d. 1)
- Kognitif Appraisal & Pemulihan Afektif Homeostasis (Half-life decay)
- Skala Kedekatan Sosial: 0 s.d. 30 (Dunbar-inspired tie strength)
- Jam Sirkadian Aktivitas 24-Jam: Fluktuasi bimodal (puncak 10:00 & 20:00, palung tidur 01:00-05:00)
- Variasi Kronotipe (Morning Lark vs Night Owl) & Resiliensi Tidur (Orderliness)
- Simulasi Swarm Predictive Sandbox & Deteksi Anomali / Deadlock (Burnout, Hysteria Spiral, Anomie)
- Integrasi Parameter Terkalibrasi untuk Downstream Agent 10 (Nested Logit & DDM)
"""

import math
import random
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, model_validator


class EkmanEmotions(BaseModel):
    """
    7 Dimensi Emosi Dasar Paul Ekman (1971, 1992).
    Masing-masing bernilai kontinu dalam rentang [0.0, 1.0].
    """
    joy: float = Field(default=0.5, ge=0.0, le=1.0, description="Kegembiraan, afeksi positif, euforia")
    sadness: float = Field(default=0.1, ge=0.0, le=1.0, description="Kesedihan, duka, keputusasaan")
    anger: float = Field(default=0.1, ge=0.0, le=1.0, description="Kemarahan, frustrasi, agresi")
    fear: float = Field(default=0.1, ge=0.0, le=1.0, description="Ketakutan, kecemasan, rasa terancam")
    disgust: float = Field(default=0.05, ge=0.0, le=1.0, description="Kejijikan, penolakan moral / konten")
    surprise: float = Field(default=0.2, ge=0.0, le=1.0, description="Keterkejutan, keheranan terhadap anomali")
    trust: float = Field(default=0.6, ge=0.0, le=1.0, description="Kepercayaan sosial, rasa aman antar-agen")

    def to_dict(self) -> Dict[str, float]:
        return {
            "joy": round(self.joy, 4),
            "sadness": round(self.sadness, 4),
            "anger": round(self.anger, 4),
            "fear": round(self.fear, 4),
            "disgust": round(self.disgust, 4),
            "surprise": round(self.surprise, 4),
            "trust": round(self.trust, 4),
        }

    def valence_arousal(self) -> Dict[str, float]:
        """
        Memetakan 7 emosi Ekman ke Model Sirkumpleks Russell (PAD):
        - Valence: [-1.0, 1.0] (Positif vs Negatif)
        - Arousal: [0.0, 1.0] (Ketenangan vs Aktivasi Fisiologis)
        - Dominance: [-1.0, 1.0] (Rasa kendali / agensi subyektif)
        """
        # Positif: joy, trust. Negatif: sadness, anger, fear, disgust
        pos_weight = (self.joy * 1.2 + self.trust * 0.8) / 2.0
        neg_weight = (self.sadness * 0.9 + self.anger * 1.1 + self.fear * 1.2 + self.disgust * 0.8) / 4.0
        valence = max(-1.0, min(1.0, (pos_weight - neg_weight) * 1.5))

        # Arousal diaktifkan oleh kemarahan, ketakutan, kejutan, dan kegembiraan
        arousal = max(0.0, min(1.0, (self.anger * 1.1 + self.fear * 1.2 + self.surprise * 0.9 + self.joy * 0.8) / 4.0))

        # Dominance ditingkatkan oleh anger dan joy, ditekan oleh fear dan sadness
        dominance = max(-1.0, min(1.0, ((self.anger * 0.8 + self.joy * 0.7 + self.trust * 0.5) - (self.fear * 1.1 + self.sadness * 0.9)) / 2.0))

        return {
            "valence": round(valence, 4),
            "arousal": round(arousal, 4),
            "dominance": round(dominance, 4)
        }

    def primary_emotion(self) -> Tuple[str, float]:
        """Mengembalikan emosi dengan intensitas tertinggi."""
        d = self.to_dict()
        top_name = max(d.keys(), key=lambda k: d[k])
        return top_name, d[top_name]


class HumanoidNeedsState(BaseModel):
    """
    State Kebutuhan Dasar System 1 dan Status Afektif Agen Humanoid.
    Mendukung alias legacy (social -> social_drive, entertainment -> stimulation).
    """
    energy: float = Field(default=1.0, ge=0.0, le=1.0, description="Stamina fisik/kognitif agen (1.0 = bugar, 0.0 = lelah ekstrem)")
    social_drive: float = Field(default=0.8, ge=0.0, le=1.0, description="Kebutuhan interaksi sosial / afiliasi")
    stimulation: float = Field(default=0.7, ge=0.0, le=1.0, description="Kebutuhan stimulasi kognitif / rasa ingin tahu")
    achievement: float = Field(default=0.5, ge=0.0, le=1.0, description="Kebutuhan pencapaian / rekognisi / status sosial")
    social_closeness: float = Field(default=15.0, ge=0.0, le=30.0, description="Kedekatan sosial jaringan (Dunbar tie strength scale)")
    emotions: EkmanEmotions = Field(default_factory=EkmanEmotions, description="Vektor 7 emosi dasar Paul Ekman")
    circadian_factor: float = Field(default=1.0, description="Pengali efektivitas sirkadian saat ini")
    sleep_debt: float = Field(default=0.0, ge=0.0, le=24.0, description="Akumulasi hutang tidur (jam)")
    chronotype_offset: float = Field(default=0.0, ge=-4.0, le=4.0, description="Pergeseran kronotipe (-3 = early bird, +3 = night owl)")
    orderliness_resilience: float = Field(default=0.7, ge=0.0, le=1.0, description="Resiliensi siklus tidur berbasis orderliness")

    @model_validator(mode='before')
    @classmethod
    def remap_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'social' in data and 'social_drive' not in data:
                data['social_drive'] = data['social']
            if 'entertainment' in data and 'stimulation' not in data:
                data['stimulation'] = data['entertainment']
        return data


class AppraisalEvent(BaseModel):
    """
    Stimulus lingkungan atau interaksi sosial yang memicu evaluasi kognitif (appraisal).
    """
    event_type: str = Field(default="social_positive", description="Tipe peristiwa: threat_shock, social_positive, social_negative, content_toxic, content_novel, isolation, custom")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Kekuatan atau intensitas stimulus")
    valence_shift: float = Field(default=0.0, ge=-1.0, le=1.0, description="Pergeseran valensi eksplisit untuk event custom")
    description: str = Field(default="", description="Deskripsi singkat konteks peristiwa")


class HumanoidAnomalyReport(BaseModel):
    """
    Laporan identifikasi anomali, deadlock, dan kondisi patologis swarm humanoid.
    """
    burnout_detected: bool = Field(default=False, description="Kelelahan kronis massal (rata-rata energi populasi < 0.15)")
    hysteria_spiral_detected: bool = Field(default=False, description="Spiral kepanikan / kemarahan kolektif (fear/anger > 0.70 dengan varians rendah)")
    anomie_detected: bool = Field(default=False, description="Alienasi sosial massal (social_drive < 0.15 dan isolasi tinggi)")
    circadian_desync_detected: bool = Field(default=False, description="Disregulasi ritme sirkadian (kegagalan fase tidur/bangun)")
    anomaly_details: List[str] = Field(default_factory=list, description="Rincian catatan anomali yang terdeteksi")


class SwarmHumanoidSimulationResult(BaseModel):
    """
    Hasil eksekusi simulasi prediktif swarm humanoid dalam sandbox multi-jam.
    """
    total_agents: int
    total_hours: int
    collective_energy_trajectory: List[float]
    collective_social_trajectory: List[float]
    collective_emotions_trajectory: Dict[str, List[float]]
    collective_valence_trajectory: List[float]
    collective_arousal_trajectory: List[float]
    circadian_sync_index: float = Field(description="Tingkat sinkronisasi fase sirkadian populasi (0.0 s.d. 1.0)")
    exhaustion_rate: float = Field(description="Proporsi agen dengan energi kritis (< 0.15)")
    hysteria_rate: float = Field(description="Proporsi agen dalam keadaan kepanikan / amarah akut")
    anomie_rate: float = Field(description="Proporsi agen mengalami isolasi / anomie")
    homeostasis_recovery_hours: Optional[int] = Field(default=None, description="Jumlah jam yang dibutuhkan populasi untuk kembali ke baseline pasca-shock")
    anomalies: HumanoidAnomalyReport


class HumanoidNeedsEngine:
    """
    Mesin Simulasi System 1 Humanoid Needs ODE & Ekman Emotions Engine.
    Mengintegrasikan dinamika peluruhan kebutuhan homeostatis, emosi dasar Ekman,
    jam sirkadian 24-jam bimodal, dan penghitungan utilitas downstream.
    """

    def __init__(
        self,
        lambda_energy: float = 0.05,
        lambda_social: float = 0.03,
        lambda_stimulation: float = 0.04,
        lambda_achievement: float = 0.02,
        emotion_half_life_hours: float = 4.0,
        baseline_emotions: Optional[EkmanEmotions] = None,
        random_seed: Optional[int] = None
    ):
        self.lambda_energy = lambda_energy
        self.lambda_social = lambda_social
        self.lambda_stimulation = lambda_stimulation
        self.lambda_achievement = lambda_achievement
        self.emotion_half_life_hours = max(0.5, emotion_half_life_hours)
        self.emotion_decay_rate = math.log(2.0) / self.emotion_half_life_hours
        self.baseline_emotions = baseline_emotions or EkmanEmotions()
        self.rng = random.Random(random_seed)

    @classmethod
    def from_psychometrics_recommendation(
        cls,
        rec: Any,
        chronotype_offset: float = 0.0
    ) -> Tuple["HumanoidNeedsEngine", HumanoidNeedsState]:
        """
        Pabrik instansiasi terkalibrasi langsung dari rekomendasi Agent 08 (PsychometricsEngine).
        """
        if hasattr(rec, "agent_09_needs"):
            a09 = rec.agent_09_needs
        elif isinstance(rec, dict) and "agent_09_needs" in rec:
            a09 = rec["agent_09_needs"]
        elif isinstance(rec, dict):
            a09 = rec
        else:
            a09 = {}

        l_energy = float(a09.get("effective_lambda_energy", 0.05))
        l_social = float(a09.get("effective_lambda_social", 0.03))
        raw_emotions = a09.get("baseline_ekman_emotions", {})
        resilience = float(a09.get("circadian_sleep_resilience", 0.7))

        ekman = EkmanEmotions(
            joy=float(raw_emotions.get("joy", 0.5)),
            sadness=float(raw_emotions.get("sadness", 0.1)),
            anger=float(raw_emotions.get("anger", 0.1)),
            fear=float(raw_emotions.get("fear", 0.1)),
            disgust=float(raw_emotions.get("disgust", 0.05)),
            surprise=float(raw_emotions.get("surprise", 0.2)),
            trust=float(raw_emotions.get("trust", 0.6)),
        )

        engine = cls(
            lambda_energy=l_energy,
            lambda_social=l_social,
            baseline_emotions=ekman
        )

        state = HumanoidNeedsState(
            energy=1.0,
            social_drive=0.8,
            stimulation=0.7,
            achievement=0.5,
            social_closeness=15.0,
            emotions=ekman,
            chronotype_offset=chronotype_offset,
            orderliness_resilience=resilience
        )

        return engine, state

    def step_ode_decay(
        self,
        state: HumanoidNeedsState,
        dt_hours: float = 1.0,
        replenishment: Optional[Dict[str, float]] = None,
        is_sleeping: bool = False,
        current_hour: Optional[int] = None
    ) -> HumanoidNeedsState:
        """
        Solusi analitik ODE Kebutuhan Homeostatis Inhomogen:
        dN/dt = -lambda * N + R(t)
        N(t + dt) = N(t) * exp(-lambda * dt) + (R / lambda) * (1 - exp(-lambda * dt))
        """
        repl = replenishment or {}
        r_energy = repl.get("energy", 0.0)
        r_social = repl.get("social_drive", repl.get("social", 0.0))
        r_stim = repl.get("stimulation", repl.get("entertainment", 0.0))
        r_achieve = repl.get("achievement", 0.0)
        r_closeness = repl.get("social_closeness", 0.0)

        # Cek pemulihan tidur alami jika agen tidur atau berada dalam jam tidur alami
        cur_h = current_hour if current_hour is not None else 12
        eff_h = (cur_h - state.chronotype_offset) % 24.0
        in_sleep_window = (1.0 <= eff_h <= 5.5)

        new_sleep_debt = state.sleep_debt
        if is_sleeping or (in_sleep_window and state.energy < 0.85):
            # Pemulihan energi selama tidur dipercepat oleh orderliness_resilience
            sleep_recovery_rate = 0.14 * (0.6 + 0.4 * state.orderliness_resilience)
            r_energy += sleep_recovery_rate
            new_sleep_debt = max(0.0, new_sleep_debt - dt_hours * 1.2)
        else:
            if in_sleep_window:
                # Terjaga saat jam tidur menambah hutang tidur
                new_sleep_debt = min(24.0, new_sleep_debt + dt_hours * 0.2)

        def _solve_inhomogeneous_ode(current_val: float, lam: float, r: float, dt: float) -> float:
            exp_term = math.exp(-lam * dt)
            if lam > 1e-6:
                val = current_val * exp_term + (r / lam) * (1.0 - exp_term)
            else:
                val = current_val + r * dt
            return val

        # 1. Update Dimensi Kebutuhan Dasar
        new_energy = _solve_inhomogeneous_ode(state.energy, self.lambda_energy, r_energy, dt_hours)
        new_social = _solve_inhomogeneous_ode(state.social_drive, self.lambda_social, r_social, dt_hours)
        new_stim = _solve_inhomogeneous_ode(state.stimulation, self.lambda_stimulation, r_stim, dt_hours)
        new_achieve = _solve_inhomogeneous_ode(state.achievement, self.lambda_achievement, r_achieve, dt_hours)

        # 2. Skala Kedekatan Sosial Dunbar (Peluruhan lambat lambda=0.005)
        new_closeness = _solve_inhomogeneous_ode(state.social_closeness, 0.005, r_closeness, dt_hours)

        # 3. Relaksasi Emosional ke Baseline (Homeostasis Afektif)
        exp_emo = math.exp(-self.emotion_decay_rate * dt_hours)
        base = self.baseline_emotions
        cur_e = state.emotions

        emo_joy = base.joy + (cur_e.joy - base.joy) * exp_emo
        emo_sadness = base.sadness + (cur_e.sadness - base.sadness) * exp_emo
        emo_anger = base.anger + (cur_e.anger - base.anger) * exp_emo
        emo_fear = base.fear + (cur_e.fear - base.fear) * exp_emo
        emo_disgust = base.disgust + (cur_e.disgust - base.disgust) * exp_emo
        emo_surprise = base.surprise + (cur_e.surprise - base.surprise) * exp_emo
        emo_trust = base.trust + (cur_e.trust - base.trust) * exp_emo

        # 4. Somatic Coupling: Dampak defisit kebutuhan terhadap emosi
        # Kelelahan kritis (energy < 0.20) meningkatkan iritabilitas (anger & sadness), menekan joy
        if new_energy < 0.20:
            fatigue_distress = (0.20 - new_energy) / 0.20
            emo_anger += 0.15 * fatigue_distress
            emo_sadness += 0.15 * fatigue_distress
            emo_joy -= 0.20 * fatigue_distress

        # Isolasi / kelaparan sosial (social_drive < 0.20) meningkatkan sadness & kecurigaan (dampen trust)
        if new_social < 0.20:
            social_distress = (0.20 - new_social) / 0.20
            emo_sadness += 0.20 * social_distress
            emo_trust -= 0.15 * social_distress

        # Bounding ketat
        final_energy = round(max(0.01, min(1.0, new_energy)), 4)
        final_social = round(max(0.01, min(1.0, new_social)), 4)
        final_stim = round(max(0.01, min(1.0, new_stim)), 4)
        final_achieve = round(max(0.01, min(1.0, new_achieve)), 4)
        final_closeness = round(max(0.0, min(30.0, new_closeness)), 2)

        final_emotions = EkmanEmotions(
            joy=round(max(0.0, min(1.0, emo_joy)), 4),
            sadness=round(max(0.0, min(1.0, emo_sadness)), 4),
            anger=round(max(0.0, min(1.0, emo_anger)), 4),
            fear=round(max(0.0, min(1.0, emo_fear)), 4),
            disgust=round(max(0.0, min(1.0, emo_disgust)), 4),
            surprise=round(max(0.0, min(1.0, emo_surprise)), 4),
            trust=round(max(0.0, min(1.0, emo_trust)), 4),
        )

        circ_factor = self.compute_circadian_factor(cur_h, state.chronotype_offset)

        return HumanoidNeedsState(
            energy=final_energy,
            social_drive=final_social,
            stimulation=final_stim,
            achievement=final_achieve,
            social_closeness=final_closeness,
            emotions=final_emotions,
            circadian_factor=circ_factor,
            sleep_debt=round(new_sleep_debt, 2),
            chronotype_offset=state.chronotype_offset,
            orderliness_resilience=state.orderliness_resilience
        )

    def step_ode_rk2(
        self,
        state: HumanoidNeedsState,
        dt_hours: float = 1.0,
        replenishment: Optional[Dict[str, float]] = None
    ) -> HumanoidNeedsState:
        """
        Solusi numerik Runge-Kutta Orde-2 (Metode Midpoint) untuk verifikasi numerik ODE:
        k1 = f(y_n)
        k2 = f(y_n + 0.5 * dt * k1)
        y_{n+1} = y_n + dt * k2
        """
        repl = replenishment or {}
        r_e = repl.get("energy", 0.0)
        r_s = repl.get("social_drive", 0.0)
        r_stim = repl.get("stimulation", 0.0)

        # Midpoint step
        k1_e = -self.lambda_energy * state.energy + r_e
        k1_s = -self.lambda_social * state.social_drive + r_s
        k1_stim = -self.lambda_stimulation * state.stimulation + r_stim

        mid_e = state.energy + 0.5 * dt_hours * k1_e
        mid_s = state.social_drive + 0.5 * dt_hours * k1_s
        mid_stim = state.stimulation + 0.5 * dt_hours * k1_stim

        k2_e = -self.lambda_energy * mid_e + r_e
        k2_s = -self.lambda_social * mid_s + r_s
        k2_stim = -self.lambda_stimulation * mid_stim + r_stim

        new_e = round(max(0.01, min(1.0, state.energy + dt_hours * k2_e)), 4)
        new_s = round(max(0.01, min(1.0, state.social_drive + dt_hours * k2_s)), 4)
        new_stim = round(max(0.01, min(1.0, state.stimulation + dt_hours * k2_stim)), 4)

        return HumanoidNeedsState(
            energy=new_e,
            social_drive=new_s,
            stimulation=new_stim,
            achievement=state.achievement,
            social_closeness=state.social_closeness,
            emotions=state.emotions,
            circadian_factor=state.circadian_factor,
            sleep_debt=state.sleep_debt,
            chronotype_offset=state.chronotype_offset,
            orderliness_resilience=state.orderliness_resilience
        )

    def appraise_event(self, state: HumanoidNeedsState, event: AppraisalEvent) -> HumanoidNeedsState:
        """
        Model Evaluasi Kognitif Emosional (Emotional Appraisal):
        Mentransformasikan stimulus eksternal menjadi pergeseran langsung pada 7 emosi Ekman.
        """
        cur = state.emotions
        intens = event.intensity
        t = event.event_type.lower()

        # Delta inisial
        d_joy = 0.0
        d_sadness = 0.0
        d_anger = 0.0
        d_fear = 0.0
        d_disgust = 0.0
        d_surprise = 0.0
        d_trust = 0.0

        if t == "threat_shock":
            d_fear = 0.45 * intens
            d_anger = 0.30 * intens
            d_surprise = 0.25 * intens
            d_trust = -0.40 * intens
            d_joy = -0.35 * intens
        elif t == "social_positive":
            d_joy = 0.40 * intens
            d_trust = 0.35 * intens
            d_sadness = -0.30 * intens
            d_anger = -0.25 * intens
            d_fear = -0.20 * intens
        elif t == "social_negative":
            d_anger = 0.40 * intens
            d_sadness = 0.30 * intens
            d_trust = -0.35 * intens
            d_disgust = 0.25 * intens
            d_joy = -0.30 * intens
        elif t == "content_toxic":
            d_disgust = 0.50 * intens
            d_anger = 0.30 * intens
            d_trust = -0.25 * intens
        elif t == "content_novel":
            d_surprise = 0.50 * intens
            d_joy = 0.25 * intens
        elif t == "isolation":
            d_sadness = 0.45 * intens
            d_trust = -0.25 * intens
            d_joy = -0.35 * intens
        elif t == "custom":
            if event.valence_shift >= 0.0:
                d_joy = 0.40 * event.valence_shift * intens
                d_trust = 0.30 * event.valence_shift * intens
            else:
                d_sadness = 0.40 * abs(event.valence_shift) * intens
                d_anger = 0.30 * abs(event.valence_shift) * intens
                d_trust = -0.30 * abs(event.valence_shift) * intens

        new_emotions = EkmanEmotions(
            joy=round(max(0.0, min(1.0, cur.joy + d_joy)), 4),
            sadness=round(max(0.0, min(1.0, cur.sadness + d_sadness)), 4),
            anger=round(max(0.0, min(1.0, cur.anger + d_anger)), 4),
            fear=round(max(0.0, min(1.0, cur.fear + d_fear)), 4),
            disgust=round(max(0.0, min(1.0, cur.disgust + d_disgust)), 4),
            surprise=round(max(0.0, min(1.0, cur.surprise + d_surprise)), 4),
            trust=round(max(0.0, min(1.0, cur.trust + d_trust)), 4),
        )

        return HumanoidNeedsState(
            energy=state.energy,
            social_drive=state.social_drive,
            stimulation=state.stimulation,
            achievement=state.achievement,
            social_closeness=state.social_closeness,
            emotions=new_emotions,
            circadian_factor=state.circadian_factor,
            sleep_debt=state.sleep_debt,
            chronotype_offset=state.chronotype_offset,
            orderliness_resilience=state.orderliness_resilience
        )

    def compute_circadian_factor(self, hour_of_day: int, chronotype_offset: float = 0.0) -> float:
        """
        Kurva sirkadian 24-jam bimodal realistis:
        - Puncak pagi: ~10:00 - 11:00
        - Puncak malam: ~20:00 - 21:00
        - Palung tidur (rest mode): 01:00 - 05:00 (ditekan hingga 0.05)
        - Mendukung offset kronotipe (-3 hingga +3 jam).
        """
        h = (float(hour_of_day) - chronotype_offset) % 24.0

        # Dua puncak Gauss pada 10.5 dan 20.5
        peak1 = math.exp(-((h - 10.5) ** 2) / 10.0)
        peak2 = math.exp(-((h - 20.5) ** 2) / 8.0)
        factor = 0.25 + 0.55 * peak1 + 0.60 * peak2

        # Mode tidur aktif antara 01:00 hingga 05:30
        if 1.0 <= h <= 5.5:
            factor *= 0.20

        return round(max(0.05, min(1.0, factor)), 3)

    def calculate_post_probability(self, state: HumanoidNeedsState, hour: int) -> float:
        """
        Menghitung probabilitas agen melakukan posting / aktivitas produksi.
        Dipengaruhi oleh sisa energi, dorongan stimulasi, dan jam sirkadian.
        (Menjaga kompatibilitas penuh dengan versi legacy).
        """
        circ = self.compute_circadian_factor(hour, state.chronotype_offset)
        fear_penalty = 1.0 - 0.4 * state.emotions.fear
        prob = (state.energy * 0.40 + state.social_drive * 0.30 + state.stimulation * 0.30) * fear_penalty
        return round(max(0.0, min(1.0, prob * circ)), 4)

    def calculate_action_probabilities(self, state: HumanoidNeedsState, hour: int) -> Dict[str, float]:
        """
        Menghasilkan distribusi probabilitas aksi diskrit yang dinormalisasi:
        - post: penyiaran konten baru (produksi)
        - reply: interaksi balasan percakapan (afiliasi)
        - like: validasi ringan (apresiasi afektif)
        - browse: konsumsi pasif / lurker dwell
        - rest: istirahat / mode tidur biologis
        """
        circ = self.compute_circadian_factor(hour, state.chronotype_offset)
        va = state.emotions.valence_arousal()
        v = va["valence"]
        a = va["arousal"]

        # Bobot mentah untuk masing-masing opsi
        w_post = max(0.01, (0.35 * state.energy + 0.35 * state.stimulation + 0.30 * state.achievement) * circ * (1.0 - 0.5 * state.emotions.fear))
        w_reply = max(0.01, (0.30 * state.energy + 0.50 * state.social_drive + 0.20 * state.emotions.trust) * circ)
        w_like = max(0.01, (0.20 * state.energy + 0.40 * state.emotions.joy + 0.40 * state.emotions.trust) * circ)
        w_browse = max(0.02, (0.20 * state.energy + 0.60 * (1.0 - state.stimulation) + 0.20 * state.emotions.surprise) * max(0.2, circ))

        # Bobot istirahat tinggi jika jam tidur atau kelelahan akut
        sleep_pressure = (1.0 - circ) * 0.70 + (1.0 - state.energy) * 0.50 + (state.sleep_debt / 24.0) * 0.40
        w_rest = max(0.02, sleep_pressure)

        total = w_post + w_reply + w_like + w_browse + w_rest
        return {
            "post": round(w_post / total, 4),
            "reply": round(w_reply / total, 4),
            "like": round(w_like / total, 4),
            "browse": round(w_browse / total, 4),
            "rest": round(w_rest / total, 4)
        }

    def get_decision_utilities(self, state: HumanoidNeedsState, hour: int) -> Dict[str, Any]:
        """
        Menyediakan payload kalibrasi utilitas untuk dikonsumsi langsung oleh
        Agent 10 (Nested Logit Kenneth Train & Ratcliff DDM).
        """
        circ = self.compute_circadian_factor(hour, state.chronotype_offset)
        va = state.emotions.valence_arousal()
        valence = va["valence"]

        # Utilitas tingkat atas (Active vs Lurker)
        u_active = round(0.50 + 0.40 * state.energy + 0.30 * state.social_drive + 0.20 * state.achievement - 0.40 * state.emotions.fear - 0.30 * state.emotions.sadness, 3)
        u_lurker = round(0.50 + 0.60 * (1.0 - state.energy) + 0.50 * state.emotions.fear + 0.30 * state.emotions.disgust - 0.40 * state.social_drive, 3)

        # Utilitas aksi bersarang
        action_utilities = {
            "like": round(0.40 + 0.30 * state.emotions.joy + 0.30 * state.emotions.trust, 3),
            "retweet": round(0.30 + 0.30 * state.emotions.surprise + 0.20 * state.emotions.joy - 0.20 * state.emotions.fear, 3),
            "reply": round(0.30 + 0.35 * state.social_drive + 0.20 * state.emotions.anger + 0.15 * state.emotions.trust, 3),
            "quote": round(0.20 + 0.35 * state.achievement + 0.25 * state.emotions.anger + 0.20 * state.emotions.surprise, 3),
        }

        # Modifikasi DDM Drift Rate & Prospect Loss Aversion
        ddm_drift_mod = round(0.20 * valence - 0.15 * state.emotions.fear, 3)
        prospect_loss_mod = round(0.35 * state.emotions.fear + 0.20 * state.emotions.anger - 0.20 * state.emotions.trust, 3)

        return {
            "utility_active": u_active,
            "utility_lurker": u_lurker,
            "action_utilities": action_utilities,
            "ddm_drift_modifier": ddm_drift_mod,
            "prospect_loss_modifier": prospect_loss_mod,
            "circadian_factor": circ,
            "action_probabilities": self.calculate_action_probabilities(state, hour)
        }

    def generate_population(self, n_agents: int = 50, chronotype_diversity: bool = True) -> List[HumanoidNeedsState]:
        """
        Menghasilkan populasi agen humanoid sintetis dengan sebaran kebutuhan,
        kronotipe, dan tingkat keteraturan hidup yang bervariasi.
        """
        population: List[HumanoidNeedsState] = []
        for i in range(n_agents):
            # Sebaran kebutuhan awal
            init_energy = round(self.rng.uniform(0.75, 1.0), 3)
            init_social = round(self.rng.uniform(0.50, 0.95), 3)
            init_stim = round(self.rng.uniform(0.50, 0.90), 3)
            init_achieve = round(self.rng.uniform(0.40, 0.80), 3)
            init_closeness = round(self.rng.uniform(10.0, 25.0), 1)

            # Kronotipe: sebaran normal (-2 hingga +2 jam)
            offset = round(self.rng.gauss(0.0, 1.2), 2) if chronotype_diversity else 0.0
            offset = max(-3.5, min(3.5, offset))

            # Resiliensi keteraturan tidur
            resilience = round(self.rng.uniform(0.5, 0.95), 2)

            state = HumanoidNeedsState(
                energy=init_energy,
                social_drive=init_social,
                stimulation=init_stim,
                achievement=init_achieve,
                social_closeness=init_closeness,
                emotions=EkmanEmotions(
                    joy=round(self.rng.uniform(0.4, 0.65), 3),
                    sadness=round(self.rng.uniform(0.05, 0.2), 3),
                    anger=round(self.rng.uniform(0.05, 0.2), 3),
                    fear=round(self.rng.uniform(0.05, 0.2), 3),
                    disgust=round(self.rng.uniform(0.02, 0.1), 3),
                    surprise=round(self.rng.uniform(0.15, 0.35), 3),
                    trust=round(self.rng.uniform(0.5, 0.75), 3)
                ),
                chronotype_offset=offset,
                orderliness_resilience=resilience
            )
            population.append(state)
        return population

    def simulate_humanoid_swarm(
        self,
        population_states: Optional[List[HumanoidNeedsState]] = None,
        n_agents: int = 50,
        n_hours: int = 48,
        shock_hour: Optional[int] = None,
        shock_event: Optional[AppraisalEvent] = None,
        ambient_interaction_rate: float = 0.35
    ) -> SwarmHumanoidSimulationResult:
        """
        Menjalankan simulasi sandbox prediktif untuk populasi agen humanoid multi-jam.
        Memantau trayektori kebutuhan kolektif, emosi Ekman, siklus sirkadian,
        serta mendeteksi anomali (Burnout, Hysteria Spiral, Anomie) dan waktu pemulihan.
        """
        pop = population_states or self.generate_population(n_agents=n_agents)
        n = len(pop)

        traj_energy: List[float] = []
        traj_social: List[float] = []
        traj_emotions: Dict[str, List[float]] = {
            "joy": [], "sadness": [], "anger": [], "fear": [],
            "disgust": [], "surprise": [], "trust": []
        }
        traj_valence: List[float] = []
        traj_arousal: List[float] = []

        baseline_pre_shock_valence: Optional[float] = None
        recovery_hour_marked: Optional[int] = None

        current_pop = [s.model_copy(deep=True) for s in pop]

        for step in range(n_hours):
            hour = step % 24

            # 1. Aplikasi Shock Eksternal
            if shock_hour is not None and step == shock_hour and shock_event:
                for idx in range(n):
                    current_pop[idx] = self.appraise_event(current_pop[idx], shock_event)

            # Catat baseline valensi tepat 1 jam sebelum shock
            if shock_hour is not None and step == shock_hour - 1:
                vals = [s.emotions.valence_arousal()["valence"] for s in current_pop]
                baseline_pre_shock_valence = sum(vals) / n

            # 2. Langkah Simulasi Siklus ODE Sirkadian & Interaksi Swarm
            for idx in range(n):
                ag = current_pop[idx]
                circ = self.compute_circadian_factor(hour, ag.chronotype_offset)
                eff_h = (hour - ag.chronotype_offset) % 24.0

                # Penentuan mode istirahat vs aktivitas
                is_sleep_hour = (1.0 <= eff_h <= 5.5)
                should_sleep = is_sleep_hour or (ag.energy < 0.20)

                repl: Dict[str, float] = {}
                if not should_sleep:
                    # Peluang interaksi sosial aktif di jejaring
                    if self.rng.random() < (ambient_interaction_rate * circ):
                        repl["social_drive"] = 0.08
                        repl["stimulation"] = 0.06
                        repl["achievement"] = 0.04
                        repl["social_closeness"] = 0.20

                current_pop[idx] = self.step_ode_decay(
                    ag,
                    dt_hours=1.0,
                    replenishment=repl,
                    is_sleeping=should_sleep,
                    current_hour=hour
                )

            # 3. Agregasi Metrik Kolektif Jam Ini
            mean_energy = sum(s.energy for s in current_pop) / n
            mean_social = sum(s.social_drive for s in current_pop) / n
            mean_joy = sum(s.emotions.joy for s in current_pop) / n
            mean_sadness = sum(s.emotions.sadness for s in current_pop) / n
            mean_anger = sum(s.emotions.anger for s in current_pop) / n
            mean_fear = sum(s.emotions.fear for s in current_pop) / n
            mean_disgust = sum(s.emotions.disgust for s in current_pop) / n
            mean_surprise = sum(s.emotions.surprise for s in current_pop) / n
            mean_trust = sum(s.emotions.trust for s in current_pop) / n

            mean_val = sum(s.emotions.valence_arousal()["valence"] for s in current_pop) / n
            mean_arousal = sum(s.emotions.valence_arousal()["arousal"] for s in current_pop) / n

            traj_energy.append(round(mean_energy, 4))
            traj_social.append(round(mean_social, 4))
            traj_emotions["joy"].append(round(mean_joy, 4))
            traj_emotions["sadness"].append(round(mean_sadness, 4))
            traj_emotions["anger"].append(round(mean_anger, 4))
            traj_emotions["fear"].append(round(mean_fear, 4))
            traj_emotions["disgust"].append(round(mean_disgust, 4))
            traj_emotions["surprise"].append(round(mean_surprise, 4))
            traj_emotions["trust"].append(round(mean_trust, 4))
            traj_valence.append(round(mean_val, 4))
            traj_arousal.append(round(mean_arousal, 4))

            # 4. Pelacakan Pemulihan Homeostasis Pasca-Shock
            if shock_hour is not None and step > shock_hour and recovery_hour_marked is None:
                if baseline_pre_shock_valence is not None:
                    # Toleransi pemulihan 25% dari deviasi awal
                    if abs(mean_val - baseline_pre_shock_valence) <= 0.20:
                        recovery_hour_marked = step - shock_hour

        # 5. Analisis Anomali & Deteksi Deadlock
        exhaustion_count = sum(1 for s in current_pop if s.energy < 0.15)
        hysteria_count = sum(1 for s in current_pop if s.emotions.fear > 0.70 or s.emotions.anger > 0.70)
        anomie_count = sum(1 for s in current_pop if s.social_drive < 0.15)

        exhaustion_rate = round(exhaustion_count / n, 4)
        hysteria_rate = round(hysteria_count / n, 4)
        anomie_rate = round(anomie_count / n, 4)

        # Varians emosi fear / anger untuk mendeteksi sinkronisasi histeria
        fear_var = sum((s.emotions.fear - traj_emotions["fear"][-1]) ** 2 for s in current_pop) / n

        anomalies = HumanoidAnomalyReport()
        if min(traj_energy) < 0.15 or exhaustion_rate > 0.40:
            anomalies.burnout_detected = True
            anomalies.anomaly_details.append(
                f"Chronic Burnout: {exhaustion_count}/{n} agen mengalami kelelahan kritis (energi < 0.15)"
            )

        if (traj_emotions["fear"][-1] > 0.65 or traj_emotions["anger"][-1] > 0.65) and fear_var < 0.05:
            anomalies.hysteria_spiral_detected = True
            anomalies.anomaly_details.append(
                f"Hysteria Spiral: Sinkronisasi kemarahan/ketakutan massal terdeteksi (varians emosi rendah {fear_var:.4f})"
            )

        if anomie_rate > 0.45:
            anomalies.anomie_detected = True
            anomalies.anomaly_details.append(
                f"Anomie Isolation: {anomie_count}/{n} agen terisolasi sosial tanpa pemulihan reciprocity"
            )

        # Circadian Sync Index: Korelasi energi dengan kurva sirkadian ideal
        ideal_circ = [self.compute_circadian_factor(t % 24) for t in range(n_hours)]
        cov = sum((traj_energy[t] - sum(traj_energy)/n_hours) * (ideal_circ[t] - sum(ideal_circ)/n_hours) for t in range(n_hours))
        std_e = math.sqrt(sum((x - sum(traj_energy)/n_hours)**2 for x in traj_energy))
        std_c = math.sqrt(sum((x - sum(ideal_circ)/n_hours)**2 for x in ideal_circ))
        sync_index = round(max(0.0, min(1.0, cov / (std_e * std_c + 1e-9))), 4) if (std_e * std_c > 0) else 0.5

        return SwarmHumanoidSimulationResult(
            total_agents=n,
            total_hours=n_hours,
            collective_energy_trajectory=traj_energy,
            collective_social_trajectory=traj_social,
            collective_emotions_trajectory=traj_emotions,
            collective_valence_trajectory=traj_valence,
            collective_arousal_trajectory=traj_arousal,
            circadian_sync_index=sync_index,
            exhaustion_rate=exhaustion_rate,
            hysteria_rate=hysteria_rate,
            anomie_rate=anomie_rate,
            homeostasis_recovery_hours=recovery_hour_marked,
            anomalies=anomalies
        )
