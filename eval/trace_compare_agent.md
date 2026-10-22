# Same question, 3 runs (agent, no cache)

**Question:** I already applied for a BIS licence and BIS has raised objections. How much time do I get to respond, and what happens if I don't?

| stage | same? | run 1 | run 2 | run 3 |
|---|---|---|---|---|
| understand_ok | yes | n/a (the agent plans its own searches) | n/a (the agent plans its own searches) | n/a (the agent plans its own searches) |
| intent | yes | None | None | None |
| tools | yes | search_documents -> search_documents | search_documents -> search_documents | search_documents -> search_documents |
| sub-queries | yes | I already applied for a BIS licence and BIS has raised objections. How much time do I get to respond, and what happens if I don't? // application objections reply time period days provisional query BIS | I already applied for a BIS licence and BIS has raised objections. How much time do I get to respond, and what happens if I don't? // application objections reply time period days provisional query BIS | I already applied for a BIS licence and BIS has raised objections. How much time do I get to respond, and what happens if I don't? // application objections reply time period days provisional query BIS |
| concept terms | yes | hearing, removal, remove, shown | hearing, removal, remove, shown | hearing, removal, remove, shown |
| retrieved per sub-query (count: top 3) | yes | 8: ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003 // 8: guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0004 | 8: ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003 // 8: guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0004 | 8: ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003 // 8: guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0004 |
| chunks sent to the LLM | yes | ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003, guide_unsatisfactory_performance::0021, guide_additional_scheme1::0011, ca_regulations_2018::0109, guide_non_conformity::0024, guide_unsatisfactory_performance::0009, guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0002, guide_unsatisfactory_performance::0006, ca_regulations_2018::0001 | ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003, guide_unsatisfactory_performance::0021, guide_additional_scheme1::0011, ca_regulations_2018::0109, guide_non_conformity::0024, guide_unsatisfactory_performance::0009, guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0002, guide_unsatisfactory_performance::0006, ca_regulations_2018::0001 | ca_regulations_2018::0004, cert_faq::0001, cert_faq::0003, guide_unsatisfactory_performance::0021, guide_additional_scheme1::0011, ca_regulations_2018::0109, guide_non_conformity::0024, guide_unsatisfactory_performance::0009, guide_unsatisfactory_performance::0004, guide_grant_of_licence::0059, ca_regulations_2018::0002, guide_unsatisfactory_performance::0006, ca_regulations_2018::0001 |
| provider | yes | gemini:gemini-3.5-flash-lite | gemini:gemini-3.5-flash-lite | gemini:gemini-3.5-flash-lite |
| fallback | yes | - | - | - |
| model said NOT_COVERED | yes | False | False | False |
| retried after NOT_COVERED | yes | False | False | False |
| regenerated (>40% removed) | yes | False | False | False |
| sentences removed by the check | yes | 0 | 0 | 0 |
| refusal reason | yes | - | - | - |
| cited sources | yes | ca_regulations_2018::0004, guide_grant_of_licence::0059 | ca_regulations_2018::0004, guide_grant_of_licence::0059 | ca_regulations_2018::0004, guide_grant_of_licence::0059 |
| answer (first line) | yes | Here's what you need to do: | Here's what you need to do: | Here's what you need to do: |

**First stage that differs:** none (all stages identical)

## Full answers

### Run 1

Here's what you need to do:

### Time given to respond to objections
* You are given **thirty days** from the date of receipt of the relevant communication from the Bureau to remove the objections raised on your application [1].
* The Bureau may extend this time for removing objections by a further period not exceeding **thirty days**, provided sufficient reasons are shown [1].

### What happens if you don't respond
* If no reply is received from your end within the stipulated period, your application will be processed for rejection in accordance with sub-regulation (6) of regulation 4 of the BIS (Conformity Assessment) Regulations, 2018, without any further notice [2].

Next step: Visit Manak Online at https://www.manakonline.in/ to submit your response to the objections within the allowed time limit.

**Sources:**
[1] BIS (Conformity Assessment) Regulations, 2018: p. 2, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/03/BIS_CA_12032019.pdf#page=2
[2] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): Annexure-VI > Scheme-I > 4. In case no reply is received from your end within the stipulat, p. 54, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=54

### Run 2

Here's what you need to do:

### Time given to respond to objections
* You are given **thirty days** from the date of receipt of the relevant communication from the Bureau to remove the objections raised on your application [1].
* The Bureau may extend this time for removing objections by a further period not exceeding **thirty days**, provided sufficient reasons are shown [1].

### What happens if you don't respond
* If no reply is received from your end within the stipulated period, your application will be processed for rejection in accordance with sub-regulation (6) of regulation 4 of the BIS (Conformity Assessment) Regulations, 2018, without any further notice [2].

Next step: Visit Manak Online at https://www.manakonline.in/ to submit your response to the objections within the allowed time limit.

**Sources:**
[1] BIS (Conformity Assessment) Regulations, 2018: p. 2, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/03/BIS_CA_12032019.pdf#page=2
[2] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): Annexure-VI > Scheme-I > 4. In case no reply is received from your end within the stipulat, p. 54, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=54

### Run 3

Here's what you need to do:

### Time given to respond to objections
* You are given **thirty days** from the date of receipt of the relevant communication from the Bureau to remove the objections raised on your application [1].
* The Bureau may extend this time for removing objections by a further period not exceeding **thirty days**, provided sufficient reasons are shown [1].

### What happens if you don't respond
* If no reply is received from your end within the stipulated period, your application will be processed for rejection in accordance with sub-regulation (6) of regulation 4 of the BIS (Conformity Assessment) Regulations, 2018, without any further notice [2].

Next step: Visit Manak Online at https://www.manakonline.in/ to submit your response to the objections within the allowed time limit.

**Sources:**
[1] BIS (Conformity Assessment) Regulations, 2018: p. 2, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/03/BIS_CA_12032019.pdf#page=2
[2] Guidelines for Grant of Licence (Scheme I, 25 Feb 2026): Annexure-VI > Scheme-I > 4. In case no reply is received from your end within the stipulat, p. 54, dated 2026-02-25 | https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf#page=54
