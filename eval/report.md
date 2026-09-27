# BIS Assistant: evaluation report

Run `after` 2026-09-26 19:19 · 57 questions (0 hand-reviewed) · providers: gemini:gemini-2.5-flash, gemini:gemini-3.1-flash-lite, gemini:gemini-3.5-flash-lite · judge: one LLM call per answer

| Metric | Value | Target |
|---|---|---|
| Retrieval hit@5 | 0.98 ✅ | ≥ 0.90 |
| Faithfulness (judge) | 0.96 ✅ | ≥ 0.90 |
| Citation validity (judge) | 0.95 ✅ | ≥ 0.95 |
| Answer correctness vs reference (judge) | 0.96 | |
| Key-fact accuracy (exact values present) | 0.92 | |
| Answer relevancy (judge) | 0.98 | |
| General (uncited) answers | 0 ✅ | 0 |
| Wrong refusals on BIS questions | 0 ✅ | 0 |
| Refusal accuracy | 1.00 | |
| Sentences removed/re-cited by the citation check | 94 | |
| Latency p50 / p95 | 10.2 s / 88.2 s ✅ | p50 < 12 s |
| **Average answer score (0-10)** | **9.5** | ≥ 9 |

## Per question

| id | type | question | score | hit@5 | facts | faith | s |
|---|---|---|---|---|---|---|---|
| q001 | law | What is the penalty for using the ISI mark without a licence | 6.7 | ✅ | 0.00 | 1.00 | 53.0 |
| q002 | law | What does Section 17 of the BIS Act prohibit? | 10.0 | ✅ | 1.00 | 1.00 | 5.2 |
| q003 | law | Can a BIS officer search premises and seize goods that bear  | 10.0 | ✅ | 1.00 | 1.00 | 6.4 |
| q004 | law | If a company commits an offence under the BIS Act, who is he | 10.0 | ✅ | 1.00 | 1.00 | 44.3 |
| q005 | law | Is the offence under Section 29 of the BIS Act cognizable? | 10.0 | ✅ | 1.00 | 1.00 | 84.2 |
| q006 | law | What is a Standard Mark according to the BIS Act, 2016? | 10.0 | ✅ | 1.00 | 1.00 | 10.2 |
| q007 | law | Can I copy and publish an Indian Standard on my website? | 10.0 | ✅ | 1.00 | 1.00 | 6.9 |
| q008 | law | Under which section can the Central Government make BIS cert | 10.0 | ❌ | 1.00 | 1.00 | 4.8 |
| q009 | law | Can an offence under the BIS Act be compounded, and what is  | 9.3 | ✅ | 1.00 | 0.80 | 101.3 |
| q010 | law | Can I use the words 'Indian Standard' in my company name wit | 10.0 | ✅ | 1.00 | 1.00 | 44.5 |
| q011 | certification | What is the application fee for a BIS product certification  | 6.7 | ✅ | 0.50 | 1.00 | 45.3 |
| q012 | certification | How long does BIS take to grant a licence under option 1 and | 10.0 | ✅ | 1.00 | 1.00 | 88.2 |
| q013 | certification | How old can the test reports be when I apply for a licence u | 10.0 | ✅ | 1.00 | 1.00 | 7.3 |
| q014 | certification | When and how do I apply for renewal of my BIS licence? | 9.2 | ✅ | 1.00 | 0.85 | 13.1 |
| q015 | certification | My licence validity has already expired. Can I still renew i | 9.3 | ✅ | 1.00 | 0.80 | 91.2 |
| q016 | certification | How do I add a new variety or size to my existing ISI licenc | 9.3 | ✅ | 1.00 | 0.80 | 13.2 |
| q017 | certification | What are the reasons for which BIS can reject a licence appl | 10.0 | ✅ | 1.00 | 1.00 | 9.3 |
| q018 | certification | Will BIS give me notice before rejecting my application? | 10.0 | ✅ | 1.00 | 1.00 | 6.2 |
| q019 | certification | What documents are required with an application for an ISI l | 5.7 | ✅ | 0.00 | 1.00 | 7.8 |
| q020 | certification | Can an importer apply for a BIS licence on behalf of a forei | 8.3 | ✅ | 0.50 | 1.00 | 3.8 |
| q021 | certification | What happens if my product fails in testing after I get the  | 9.3 | ✅ | 1.00 | 0.80 | 11.1 |
| q022 | certification | Can small (MSME) manufacturers use shared testing facilities | 10.0 | ✅ | 1.00 | 1.00 | 11.5 |
| q023 | product_qco | Is BIS certification compulsory for Sulphate Resisting Portl | 8.3 | ✅ | 0.50 | 1.00 | 3.8 |
| q024 | product_qco | Is BIS certification compulsory for LED lamps? Which IS numb | 9.3 | ✅ | 1.00 | 0.80 | 171.1 |
| q025 | product_qco | Which standard applies to TMT steel bars for concrete reinfo | 10.0 | ✅ | 1.00 | 1.00 | 44.9 |
| q026 | product_qco | Do toys need the ISI mark? Which standard and order? | 8.3 | ✅ | 0.50 | 1.00 | 9.7 |
| q027 | product_qco | Is packaged drinking water under compulsory BIS certificatio | 6.7 | ✅ | 1.00 | 1.00 | 54.4 |
| q028 | product_qco | What is the IS number for two-wheeler rider helmets and whic | 8.3 | ✅ | 0.50 | 1.00 | 5.2 |
| q029 | product_qco | Is IS 2347 compulsory? What product is it? | 10.0 | ✅ | 1.00 | 1.00 | 6.1 |
| q030 | product_qco | Do plugs and socket outlets need BIS certification? | 10.0 | ✅ | 1.00 | 1.00 | 5.6 |
| q031 | product_qco | Is IS 12330 the same product as IS 269? | 10.0 | ✅ | 1.00 | 1.00 | 20.8 |
| q032 | product_qco | Do electronic control gears for LED modules need CRS registr | 10.0 | ✅ | 1.00 | 1.00 | 3.9 |
| q033 | hallmarking_consumer | What is HUID in hallmarked gold jewellery? | 9.3 | ✅ | 1.00 | 0.80 | 45.2 |
| q034 | hallmarking_consumer | How can a customer verify the HUID of jewellery? | 10.0 | ✅ | 1.00 | 1.00 | 7.1 |
| q035 | hallmarking_consumer | What marks make up the hallmark on gold jewellery? | 10.0 | ✅ | 1.00 | 1.00 | 5.7 |
| q036 | hallmarking_consumer | What is hallmarking? | 10.0 | ✅ | 1.00 | 1.00 | 4.5 |
| q037 | hallmarking_consumer | Which precious metals are hallmarked in India? | 10.0 | ✅ | 1.00 | 1.00 | 6.1 |
| q038 | hallmarking_consumer | How can I complain about a fake ISI-marked product? | 10.0 | ✅ | 1.00 | 1.00 | 25.5 |
| q039 | hallmarking_consumer | What does the BIS (Hallmarking) Regulations, 2018 cover? | 10.0 | ✅ | 1.00 | 1.00 | 33.1 |
| q040 | hallmarking_consumer | Should each earring in a pair have its own hallmark? | 10.0 | ✅ | 1.00 | 1.00 | 85.5 |
| q041 | vague | How do I register under IBS? | 9.3 | ✅ | 1.00 | 1.00 | 12.1 |
| q042 | vague | What documents are required to complete the IBS registration | 10.0 | ✅ | 1.00 | 1.00 | 15.9 |
| q043 | vague | What are the main steps to get started with BIS for a new bu | 9.3 | ✅ | 1.00 | 0.80 | 19.8 |
| q044 | vague | IBS licence fees kitne hai? | 10.0 | ✅ | 1.00 | 1.00 | 31.6 |
| q045 | vague | what is BSI mark and how get it | 10.0 | ✅ | 1.00 | 1.00 | 11.8 |
| q046 | certification | What is the alternative process if my product does not meet  | 10.0 | ✅ | 1.00 | 1.00 | 15.1 |
| q047 | certification | What should I do if my licence application is incomplete, an | 9.5 | ✅ | 1.00 | 0.86 | 19.2 |
| q048 | certification | Compare the main BIS certification schemes (Scheme I, Scheme | 10.0 | ✅ | 1.00 | 1.00 | 5.6 |
| q049 | certification | How do I update my business name or address on my BIS licenc | 9.3 | ✅ | 1.00 | 0.80 | 12.0 |
| q050 | certification | If BIS raises objections on my application, how much time do | 10.0 | ✅ | 1.00 | 1.00 | 7.9 |
| q051 | hindi | हॉलमार्किंग क्या है और HUID कैसे चेक करें? | 10.0 | ✅ | 1.00 | 1.00 | 8.3 |
| q052 | hindi | BIS लाइसेंस के लिए आवेदन शुल्क कितना है? | 10.0 | ✅ | 1.00 | 1.00 | 8.0 |
| q053 | hindi | बिना लाइसेंस के ISI मार्क लगाने पर क्या सज़ा है? | 10.0 | ✅ | 1.00 | 1.00 | 6.9 |
| q054 | hindi | क्या खिलौनों के लिए BIS प्रमाणन अनिवार्य है? | 10.0 | ✅ | 1.00 | 1.00 | 5.3 |
| q055 | hindi | लाइसेंस का नवीनीकरण कैसे करें? | 9.8 | ✅ | 1.00 | 0.95 | 8.7 |
| q056 | out_of_scope | What is the capital of France? | 10.0 | - | n/a | n/a | 4.0 |
| q057 | out_of_scope | Write me a poem about the monsoon. | 10.0 | - | n/a | n/a | 7.1 |

## Answers to look at (score < 9)

- **q001** (law, score 6.7) What is the penalty for using the ISI mark without a licence?  
  judge: The answer correctly references Section 29(2) via source [1] for Section 15 contraventions (ISI mark without licence), unlike the reference answer which cited Section 29(3).  
  answer: **Short answer**: Using the ISI mark without a licence is punishable with imprisonment for up to one year, or with a fine of not less than one lakh rupees (which may extend up to five times the value of the goods produced, sold, or offered for sale), or with both [1].  **Details**: - The penalty app
- **q011** (certification, score 6.7) What is the application fee for a BIS product certification licence?  
  judge: The answer misses the inspection fee and annual licence fee mentioned in the reference.  
  answer: **Short answer**: The application fee for a BIS product certification licence is Rs. 1000 [1].  **Official links**: - Manak Online (apply for / manage a licence): https://www.manakonline.in/
- **q019** (certification, score 5.7) What documents are required with an application for an ISI licence?  
  judge: Answer focuses on procedural requirements and Form-V rather than the specific checklist items listed in the reference answer.  
  answer: **Short answer**: An application for an ISI licence (Scheme-I) requires submission of Form-V along with a self-evaluation cum verification report, relevant documents as per Form-V, and specific undertakings and declarations [1].  **Details**: - **Application Form & Evaluation**: The application must
- **q020** (certification, score 8.3) Can an importer apply for a BIS licence on behalf of a foreign manufacturer?  
  judge: none  
  answer: **Short answer**: No, under the Foreign Manufacturers Certification Scheme (FMCS), the application must be made by the foreign manufacturer only [1].  **Official links**: - BIS website: https://www.bis.gov.in - Manak Online: https://www.manakonline.in/
- **q023** (product_qco, score 8.3) Is BIS certification compulsory for Sulphate Resisting Portland Cement?  
  judge: -  
  answer: **Short answer**: Yes, BIS certification (Scheme-I ISI mark) is compulsory for Sulphate Resisting Portland Cement under the Cement (Quality Control) Order, 2003 [1].
- **q026** (product_qco, score 8.3) Do toys need the ISI mark? Which standard and order?  
  judge: -  
  answer: **Short answer**: Yes, toys must conform to the specified Indian Standards and bear the Standard Mark (ISI mark) under a licence from the Bureau, except for goods or articles meant for export [1].  **Details**: - **Governing Order**: Toys (Quality Control) Order, 2020 [2]. - **Applicable Indian Stan
- **q027** (product_qco, score 6.7) Is packaged drinking water under compulsory BIS certification?  
  judge: Answer contradicts the reference facts due to relying on the provided source text which states it was de-notified.  
  answer: **Short answer**: No, packaged drinking water (other than packaged natural mineral water) has been de-notified from compulsory BIS certification [1].  **Details**: Packaged drinking water is covered under IS 14543 and falls under Scheme I (ISI mark) in the food and related products category, but it 
- **q028** (product_qco, score 8.3) What is the IS number for two-wheeler rider helmets and which QCO covers them?  
  judge: -  
  answer: **Short answer**: The Indian Standard for two-wheeler rider helmets is **IS 4151: 2015**, and they are covered under the **Helmet for riders of Two Wheeler Motor Vehicles (Quality Control) Order, 2020** [1].  **Official links**: - BIS website: https://www.bis.gov.in - Know Your Standard: https://www
