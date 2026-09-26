# The 3 weakest answers: before and after the fixes

Quick eval, 2026-09-26. Provider: Gemini Flash-Lite (no Groq key yet).

## q001: What is the penalty for using the ISI mark without a licence?

**Expected (from the documents):** Section 29(3) of the BIS Act, 2016: contravening Section 17 is punishable with imprisonment up to two years, or fine of not less than two lakh rupees for the first contravention and not less than five lakh rupees for subsequent contraventions, which may extend up to ten times the value of goods, or both.

**Fix:** Split the BIS Act into sub-section chunks (Section 29(3) is its own chunk) + a prompt rule to quote the sub-section that names the breached section (17 → 29(3)).

| | facts | citation validity | removed / re-cited by check |
|---|---|---|---|
| before | 0.0 | 0.67 | 0 / 1 |
| after | 1.0 | 1.0 | 0 / 0 |

### Before

**Short answer**: Using the ISI mark without a licence is punishable with imprisonment for up to one year, a fine of at least one lakh rupees (extending up to five times the value of the goods produced, sold, or offered for sale), or both [1].

**Details**:
- **Offence and Fine Calculation**: If the value of the goods or articles produced or sold cannot be determined, it is presumed that one year's production was in contravention, and the annual turnover in the previous financial year is taken as the value of the goods [1].
- **Search and Seizure**: A certification officer who has reason to believe that a contravention has taken place may enter, search, and seize goods, articles, processes, systems, services, or other relevant materials and documents [2].

**Official links**:
- BIS website: https://www.bis.gov.in
- BIS CARE app (verify licence or report complaints): https://play.google.com/store/apps/details?id=com.bis.bisapp

**Sources:**
[1] Bureau of Indian Standards Act, 2016: CHAPTER V > Section 29. Penalty for contravention, p. 13, dated 2016-03-22 | https://www.bis.gov.in/wp-content/uploads/2020/12/BIS-Act-2016.pdf#page=13
[2] Bureau of Indian Standards Act, 2016: CHAPTER V > Section 28. Power to search and seizure, p. 13, dated 2016-03-22 | https://www.bis.gov.in/wp-content/uploads/2020/12/BIS-Act-2016.pdf#page=13

### After

**Short answer**: Using the Standard Mark (ISI mark) without a licence is a contravention of section 17, punishable under section 29(3) of the BIS Act, 2016, with imprisonment up to two years or with fine, or with both [1].

**Details**:
- **First contravention**: Fine shall not be less than two lakh rupees, but may extend up to ten times the value of goods or articles produced or sold or offered to be sold or affixed or applied with a Standard Mark, or both [1].
- **Second and subsequent contraventions**: Fine shall not be less than five lakh rupees, but may extend up to ten times the value of goods or articles produced or sold or offered to be sold or affixed or applied with a Standard Mark, or both [1].
- **Determination of value**: Where the value of goods or articles produced, sold, or offered to be sold cannot be determined, it shall be presumed that one year's production was in such contravention, and the annual turnover in the previous financial year shall be taken as the value [1].
- **Nature of offence**: The offence under sub-section (3) is cognizable [1].

**Official links**:
- BIS website: https://www.bis.gov.in
- BIS CARE app (verify licence, HUID, CRS R-number; complaints): https://play.google.com/store/apps/details?id=com.bis.bisapp

**Sources:**
[1] Bureau of Indian Standards Act, 2016: CHAPTER V > Section 29(3) Penalty for contravention, p. 14, dated 2016-03-22 | https://www.bis.gov.in/wp-content/uploads/2020/12/BIS-Act-2016.pdf#page=14

---

## q019: What documents are required with an application for an ISI licence?

**Expected (from the documents):** The BIS check-list requires e.g. a completely filled application form; name and address matching the Government registration document; status (large/small scale, with registration certificate for small units); the Indian Standard and varieties; manufacturing and testing facilities; test reports; and other items listed in the check-list.

**Fix:** Alternative-excerpt search now uses the 6 most similar excerpts (was: the first 6); number check uses title/section of all cited excerpts.

| | facts | citation validity | removed / re-cited by check |
|---|---|---|---|
| before | 0.0 | 0.4 | 4 / 2 |
| after | 1.0 | 0.41 | 3 / 7 |

### Before

**Short answer**: An application for an ISI licence (Scheme-I) requires submission through Form-V along with a self-evaluation cum verification report, legal documents authenticating the unit/address, test reports, and other mandatory technical and administrative documents via Manak Online [1].

**Details**:
- **Technical Documents**: Test reports (in-house or independent laboratory) covering all requirements of the Indian Standard, plant layout indicating machinery, laboratory, and storage areas, and details of major test equipment compared with the product manual are required [2].

**Step-by-step**:
1. Fill up all mandatory data-fields on the Manak Online portal [2].

**Documents, fees and timelines**:
- **Documents**: Form-V application, self-evaluation cum verification report (Annexure-I), legal and address proof, test reports, plant layout, and details of manufacturing machinery and test equipment [1].
- **Fees**: Application fee, factory inspection fee, and at least 50% of the minimum marking fee (or the entire minimum marking fee) must be deposited at the time of submission [2].
- **Timelines**: The Dealing Officer scrutinizes the application within 5 working days of the application being assigned [2].

**Official links**:
- Manak Online (apply for / manage a licence): https://www.manakonline.in/
- BIS website: https://www.bis.gov.in

**Sources:**
[1] Additional Guidelines for Scheme-I (DG Order No. 3 of 2020): 2. Submission of Application, p. 4, dated 2020-08-04 | https://www.bis.gov.in/wp-content/uploads/2020/09/BIS-DGO-No.3ofYear2020.pdf#page=4
[2] Additional Guidelines for Scheme-I (DG Order No. 3 of 2020): 2. Submission of Application, p. 4, dated 2020-08-04 | https://www.bis.gov.in/wp-content/uploads/2020/09/BIS-DGO-No.3ofYear2020.pdf#page=4

### After

**Short answer**: An application for a BIS licence (Scheme-I / ISI licence) requires submission of an online application in Form-V along with a self-evaluation cum verification report, relevant documents as per Form-V and the application checklist, and mandatory fee deposits [1].

**Details**:
- **Application Form & Portals**: Applications are submitted online via Manak Online, where mandatory data-fields must be filled and essential documents uploaded [2].

**Step-by-step**:
1. Fill out the application form (Form-V) completely on the Manak Online portal along with the self-evaluation cum verification report (Annexure-I) [1].
2. Upload all mandatory data-fields, true and genuine documents, and submit the required undertakings (such as readiness for inspection and test undertakings) [2].
3. Deposit the requisite application fee, factory inspection fee, and at least 50% of the minimum marking fee (or the entire minimum marking fee) at the time of submission [2].

**Documents, fees and timelines**:
- **Documents**:
  - Application in Form-V and self-evaluation cum verification report [1].
  - Plant layout indicating locations of manufacturing machinery, laboratory, office, workshop, storage, etc [3].
  - Details and test reports of raw materials/components and major test equipment compared with the product manual [2].
  - Test reports of the product (in-house or independent laboratory) covering all requirements of the Indian Standard [3].
  - Calibration certificates for relevant test equipment and consent letters for outsourced testing, if applicable [3].
  - Details of qualified and experienced Quality Control (QC) personnel (qualification certificates and appointment letters) [3].
  - Undertakings regarding long duration tests, verification samples, and factory inspection readiness [4].
- **Fees**: Application fee, factory inspection fee, and minimum marking fee as mandated by the system [2].
- **Timelines**: The application processing time is expected to be completed within 90 days under Option 1 and within 30 days under Option 2 from the date of receipt of the application, provided documentation and assessment are satisfactory [5].

**Official links**:
- BIS website: https://www.bis.gov.in
- Manak Online (apply for / manage a licence): https://www.manakonline.in/

**Sources:**
[1] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): 3., p. 1, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=1
[2] Additional Guidelines for Scheme-I (DG Order No. 3 of 2020): 2. Submission of Application, p. 4, dated 2020-08-04 | https://www.bis.gov.in/wp-content/uploads/2020/09/BIS-DGO-No.3ofYear2020.pdf#page=4
[3] Check-list for application to be submitted by applicant to BIS: 13. Test Report(s) a, p. 2 | https://www.bis.gov.in/wp-content/uploads/2018/11/Checklist_for_Application.pdf#page=2
[4] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): Annexure-III > Scheme-I, p. 49, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=49
[5] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): Annexure-I > 6., p. 7, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=7

---

## q015: My licence validity has already expired. Can I still renew it?

**Expected (from the documents):** Yes, within 90 days after the validity date, by paying an additional late fee of ₹5,000; the decision to renew may be deferred for up to 90 days from the validity date.

**Fix:** Duplicate citations are merged again after the citation check (same page = one number); eval now reads 'ninety' as 90.

| | facts | citation validity | removed / re-cited by check |
|---|---|---|---|
| before | 0.5 | 0.45 | 1 / 5 |
| after | 1.0 | 0.75 | 0 / 1 |

### Before

**Short answer**: Yes, you can still apply for renewal within ninety days from the last date of validity by submitting the renewal application form along with the requisite fee and a late fee of rupees five thousand [1]. If your request was made in advance to keep the licence dormant, it may be deferred for up to one year [2].

**Details**:
- **Deferment period**: If the renewal application and requisite fee are not received before the expiration of the validity, the decision to renew the licence may be deferred for up to ninety days from the date of validity [3].
- **Late fee**: If the renewal application is made after the validity of the licence, it must be accompanied by a late fee of rupees five thousand [3].
- **Dormant licence option**: A manufacturer may request to defer the expiry/renewal of the licence for a period not exceeding one year due to financial problems arising from a lack of demand, upon depositing 10% of the minimum marking fee or ₹7,000 (whichever is higher) as the cost of surprise surveillance, categorising the licence as 'dormant' [4].

**Step-by-step**:
1. Submit the renewal application form through the online portal along with the requisite fee and the late fee of ₹5,000 within ninety days of the licence validity expiry [5].
2. For a dormant licence, submit the request at least a month (30 days) in advance of the validity date along with the required fee (10% of minimum marking fee or ₹7,000, whichever is higher), and complete the renewal within the one-year deferment period [4].

**What happens if...**:
- If the renewal application along with the requisite fee and late fee is not received within ninety days (or within the one-year deferment period for dormant licences), the licence shall stand expired after the last date of its validity [3].
- Once expired, you have no right to mark or supply the product with the Standard Mark, and any continued use of the mark violates the BIS Act, 2016 [6]. However, if it expired due to non-submission or voluntary surrender, you have the option to re-apply for a fresh grant of licence within one year under simpler criteria [2].

**Official links**:
- Manak Online: https://www.manakonline.in/
- BIS website: https://www.bis.gov.in
- BIS CARE app: https://play.google.com/store/apps/details?id=com.bis.bisapp

**Sources:**
[1] Guidelines for Renewal of Licence: 2., p. 1, dated 2025-03-05 | https://www.bis.gov.in/wp-content/uploads/2025/03/RenewalGuidelines-WebsiteHosting.pdf#page=1
[2] Additional Guidelines for Scheme-I (DG Order No. 3 of 2020): 9. Renewal of License, p. 10, dated 2020-08-04 | https://www.bis.gov.in/wp-content/uploads/2020/09/BIS-DGO-No.3ofYear2020.pdf#page=10
[3] BIS (Conformity Assessment) Regulations, 2018: p. 2, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/03/BIS_CA_12032019.pdf#page=2
[4] Guidelines for Renewal of Licence: 2., p. 1, dated 2025-03-05 | https://www.bis.gov.in/wp-content/uploads/2025/03/RenewalGuidelines-WebsiteHosting.pdf#page=1
[5] Guidelines for Renewal of Licence: 2., p. 1, dated 2025-03-05 | https://www.bis.gov.in/wp-content/uploads/2025/03/RenewalGuidelines-WebsiteHosting.pdf#page=1
[6] Guidelines for Renewal of Licence: 2., p. 1, dated 2025-03-05 | https://www.bis.gov.in/wp-content/uploads/2025/03/RenewalGuidelines-WebsiteHosting.pdf#page=1

### After

**Short answer**: Yes, you can still submit a renewal application within ninety days from the last date of validity by paying the requisite fee along with a late fee of rupees five thousand [1][2].

**Details**:
- If the renewal application with the requisite fee is not received before the expiration of the validity, the decision to renew your licence may be deferred for up to ninety days from the date of validity [1][2].
- If you submit the renewal application along with the requisite fees including the late fee within this 90-day period, the licence will be renewed from the date of validity [1].
- If the renewal application and requisite fee (including late fee) are not received within ninety days from the last date of validity, your licence shall stand expired [1][2].

**Official links**:
- Manak Online (apply for / manage a licence): https://www.manakonline.in/
- BIS website: https://www.bis.gov.in

**Sources:**
[1] Guidelines for Renewal of Licence: 2., p. 1, dated 2025-03-05 | https://www.bis.gov.in/wp-content/uploads/2025/03/RenewalGuidelines-WebsiteHosting.pdf#page=1
[2] BIS (Conformity Assessment) Regulations, 2018: p. 2, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/03/BIS_CA_12032019.pdf#page=2

---
