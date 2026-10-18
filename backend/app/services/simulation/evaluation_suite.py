# backend/app/services/simulation/evaluation_suite.py
"""
Evaluation Suite:
- C2ST (Classifier Two-Sample Test) evaluator metrik.
- Type-Token Ratio (TTR) & Lexical Diversity.
- Perplexity (Proxy N-gram Language Model).
- Self-BLEU (Keberagaman teks antar agen).
- n-gram Leakage Checker (Verifikasi 0 overlapping 8-grams terhadap data seed/few-shot).
"""
from __future__ import annotations

from collections import Counter
import math
import re
from typing import Any, Dict, List, Set, Tuple


def tokenize(text: str) -> List[str]:
    """Tokenisasi kata sederhana dan bersih dari tanda baca."""
    return re.findall(r"\b\w+\b", text.lower())


def extract_ngrams(tokens: List[str], n: int) -> Set[Tuple[str, ...]]:
    """Ekstraksi himpunan n-gram dari daftar token."""
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def check_ngram_leakage(
    generated_texts: List[str],
    reference_texts: List[str],
    n: int = 8,
) -> Dict[str, Any]:
    """Memverifikasi bahwa tidak ada n-gram (default: 8-gram) yang bocor/kembar dari reference_texts."""
    ref_ngrams: Set[Tuple[str, ...]] = set()
    for text in reference_texts:
        tokens = tokenize(text)
        ref_ngrams.update(extract_ngrams(tokens, n))

    leaked_ngrams: List[str] = []
    for text in generated_texts:
        tokens = tokenize(text)
        gen_ngrams = extract_ngrams(tokens, n)
        overlap = gen_ngrams.intersection(ref_ngrams)
        for ng in overlap:
            leaked_ngrams.append(" ".join(ng))

    return {
        "leakage_detected": len(leaked_ngrams) > 0,
        "overlap_count": len(leaked_ngrams),
        "overlapping_ngrams": leaked_ngrams,
        "checked_n": n,
    }


def compute_ttr(texts: List[str]) -> float:
    """Type-Token Ratio (TTR) agregat."""
    all_tokens = []
    for t in texts:
        all_tokens.extend(tokenize(t))
    if not all_tokens:
        return 0.0
    return round(len(set(all_tokens)) / len(all_tokens), 4)


def compute_lexical_diversity_mtld(tokens: List[str], threshold: float = 0.72) -> float:
    """Measure of Textual Lexical Diversity (MTLD) proxy."""
    if len(tokens) < 10:
        return 0.0

    factors = 0
    start = 0
    for i in range(1, len(tokens) + 1):
        sub_tokens = tokens[start:i]
        ttr = len(set(sub_tokens)) / len(sub_tokens)
        if ttr <= threshold:
            factors += 1
            start = i

    # Sisa fraksi
    if start < len(tokens):
        sub_tokens = tokens[start:]
        partial_ttr = len(set(sub_tokens)) / len(sub_tokens)
        fraction = (1.0 - partial_ttr) / (1.0 - threshold) if partial_ttr < 1.0 else 0.0
        factors += max(0.0, fraction)

    return round(len(tokens) / max(1.0, factors), 2)


def compute_sentence_bleu_proxy(hypothesis: List[str], reference: List[str], max_n: int = 3) -> float:
    """Proxy BLEU sederhana antar dua kalimat tokenized (1 s.d. max_n gram)."""
    if not hypothesis or not reference:
        return 0.0

    precisions = []
    for n in range(1, max_n + 1):
        hyp_ngrams = extract_ngrams(hypothesis, n)
        ref_ngrams = extract_ngrams(reference, n)
        if not hyp_ngrams:
            precisions.append(0.001)
            continue
        overlap = len(hyp_ngrams.intersection(ref_ngrams))
        precisions.append((overlap + 0.01) / (len(hyp_ngrams) + 0.01))

    # Brevity penalty
    bp = math.exp(min(0.0, 1.0 - len(reference) / max(1, len(hypothesis))))
    geom_mean = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
    return round(bp * geom_mean, 4)


def compute_self_bleu(texts: List[str], sample_size: int = 50) -> float:
    """Mengukur Self-BLEU untuk mendeteksi repetisi mode-collapse dalam output sintetis."""
    tokenized_texts = [tokenize(t) for t in texts if len(tokenize(t)) >= 3]
    if len(tokenized_texts) < 2:
        return 0.0

    scores = []
    sample = tokenized_texts[:sample_size]
    for i, hyp in enumerate(sample):
        refs = [ref for j, ref in enumerate(sample) if i != j]
        # Hitung rerata skor terhadap referensi lain
        doc_scores = [compute_sentence_bleu_proxy(hyp, ref) for ref in refs[:10]]
        if doc_scores:
            scores.append(sum(doc_scores) / len(doc_scores))

    return round(sum(scores) / len(scores), 4) if scores else 0.0


def compute_proxy_perplexity(texts: List[str]) -> float:
    """Proxy Perplexity berbasis bigram Laplace smoothed model."""
    tokens = []
    for t in texts:
        tokens.extend(tokenize(t))
    if len(tokens) < 5:
        return 1.0

    vocab = set(tokens)
    v_size = len(vocab)
    bigrams = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
    unigram_counts = Counter(tokens)
    bigram_counts = Counter(bigrams)

    log_prob_sum = 0.0
    for w1, w2 in bigrams:
        # Laplace add-1 smoothing
        prob = (bigram_counts.get((w1, w2), 0) + 1) / (unigram_counts.get(w1, 0) + v_size)
        log_prob_sum += math.log(prob)

    avg_neg_log_prob = -log_prob_sum / len(bigrams)
    # Perplexity = exp(entropy)
    ppl = math.exp(min(10.0, avg_neg_log_prob))
    return round(ppl, 2)


def evaluate_c2st_proxy(
    synthetic_texts: List[str],
    human_texts: List[str],
) -> Dict[str, Any]:
    """Classifier Two-Sample Test (C2ST) Feature Proxy.
    Menggunakan ekstraksi fitur statistik (panjang kata, panjang karakter, TTR, proporsi tanda baca)
    untuk menguji apakah teks sintetis dapat dibedakan dengan mudah dari teks manusia.
    Skor mendekati 0.50 menandakan indistinguishable (sangat bagus).
    """
    def extract_features(text: str) -> List[float]:
        tokens = tokenize(text)
        n_tok = len(tokens)
        avg_word_len = sum(len(t) for t in tokens) / max(1, n_tok)
        punct_count = len(re.findall(r"[^\w\s]", text))
        return [float(n_tok), float(avg_word_len), float(punct_count)]

    syn_feats = [extract_features(t) for t in synthetic_texts if t.strip()]
    hum_feats = [extract_features(t) for t in human_texts if t.strip()]

    if not syn_feats or not hum_feats:
        return {"c2st_accuracy": 0.50, "distinguishable": False}

    # Rata-rata fitur
    avg_syn = [sum(f[i] for f in syn_feats) / len(syn_feats) for i in range(3)]
    avg_hum = [sum(f[i] for f in hum_feats) / len(hum_feats) for i in range(3)]

    # Normalized distance antar centroid fitur
    diffs = [abs(avg_syn[i] - avg_hum[i]) / max(0.1, abs(avg_hum[i]) + 0.1) for i in range(3)]
    mean_discrepancy = sum(diffs) / len(diffs)

    # Akurasi diskriminasi perkiraan: 0.5 (chance) + 0.5 * min(1.0, discrepancy)
    estimated_acc = round(0.50 + 0.40 * min(1.0, mean_discrepancy), 3)

    return {
        "c2st_accuracy": estimated_acc,
        "distinguishable": estimated_acc > 0.75,
        "feature_discrepancy": round(mean_discrepancy, 3),
    }


class EvaluationSuite:
    """Suite evaluasi terpadu untuk kualitas & etika teks sintetis."""

    def evaluate_batch(
        self,
        generated_texts: List[str],
        reference_texts: Optional[List[str]] = None,
        human_comparison_texts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        ttr = compute_ttr(generated_texts)
        all_tokens = []
        for t in generated_texts:
            all_tokens.extend(tokenize(t))
        mtld = compute_lexical_diversity_mtld(all_tokens)
        self_bleu = compute_self_bleu(generated_texts)
        ppl = compute_proxy_perplexity(generated_texts)

        results: Dict[str, Any] = {
            "type_token_ratio": ttr,
            "lexical_diversity_mtld": mtld,
            "self_bleu": self_bleu,
            "perplexity_proxy": ppl,
            "sample_count": len(generated_texts),
        }

        if reference_texts:
            leakage = check_ngram_leakage(generated_texts, reference_texts, n=8)
            results["leakage_check"] = leakage

        if human_comparison_texts:
            c2st = evaluate_c2st_proxy(generated_texts, human_comparison_texts)
            results["c2st_evaluation"] = c2st

        return results
