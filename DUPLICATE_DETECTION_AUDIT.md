# 🧼 Phase 22F: Near-Duplicate Detection Audit Report

This audit inspects the deduplication implementation utilized during Phase 21C ([`DATA_QUALITY_REPORT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/DATA_QUALITY_REPORT.md)).

---

## 🔍 Audit Inspection of Phase 21C Deduplication Code

1. **Phase 21C Claim**:
   - The Phase 21C data quality report stated that near-duplicate detection was performed using *"Jaccard similarity > 0.90 on token sets"*.

2. **Source Code Inspection**:
   - Inspection of the actual execution code reveals:
     ```python
     for idx, row in df_dedup.iterrows():
         snippet = re.sub(r'\W+', '', row['Clean_Text'][:400].lower())
         h = hashlib.md5(snippet.encode('utf-8')).hexdigest()
         if h in near_dup_hashes:
             near_duplicates_count += 1
         else:
             near_dup_hashes.add(h)
             unique_rows.append(row)
     ```

3. **Audit Finding**:
   - **Methodology Discrepancy**: The code executed **MD5 snippet hashing over normalized leading text (first 400 characters)**, NOT pairwise token Jaccard similarity ($|A \cap B| / |A \cup B| > 0.90$) or MinHash/LSH.
   - **Effectiveness**: The 400-char MD5 snippet hash successfully identified and purged **55 resumes** with identical candidate headers, contact details, or template prefixes.
   - **Correction**: Describing MD5 snippet hashing as "token Jaccard similarity > 0.90" was inaccurate.

---

## 🛠️ Recommended Methodology for Future Dataset Builds

For future dataset ingestion iterations (without modifying the current Phase 21/22 dataset splits), the following two-stage near-duplicate detection protocol is recommended:

1. **Stage 1: MinHash + LSH (Locality-Sensitive Hashing)**:
   - Compute 128 MinHash permutations over 3-shingle character/word tokens.
   - Query LSH index with Jaccard threshold $t = 0.85$.
2. **Stage 2: Pairwise Token Jaccard Verification**:
   - For candidate pairs flagged by LSH, calculate exact Jaccard token overlap:
     $$\text{Jaccard}(A, B) = \frac{|T_A \cap T_B|}{|T_A \cup T_B|}$$
   - Purge resume $B$ if $\text{Jaccard}(A, B) \ge 0.90$.

---

> [!IMPORTANT]
> In accordance with Phase 22 rules, existing dataset splits (`train.csv`, `val.csv`, `test.csv`) remain unchanged and intact.

---

*Phase 22F Near-Duplicate Detection Audit complete.*
