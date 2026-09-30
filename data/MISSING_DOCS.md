# Documents I could not download: please download them by hand

Save each file exactly under the path shown. Anything in `data/manual/` is added to the knowledge base
on the next re-index (`python scripts/parse.py && python scripts/chunk.py && python scripts/build_index.py`,
or `POST /admin/reindex`).

These fail because bis.gov.in returns **HTTP 403 for the whole `/PDF/` folder**, including the links on
BIS's own pages. A normal browser may also be blocked; if so, look for the same title elsewhere on
bis.gov.in or India Code.

- [ ] Operating Manual for Product Certification (older, pre-2018 procedure)
      URL: https://bis.gov.in/PDF/pdf/rti/operating_manual.pdf
      Save as: `data/manual/certification/operating_manual_product_cert.pdf`
- [ ] Enforcement of BIS Act, 2016
      URL: https://www.bis.gov.in/PDF/bs/Act_Enforcement.pdf
      Save as: `data/manual/law/bis_act_enforcement.pdf`
- [ ] BIS (Powers and Duties of Director General) Regulations, 2018 (priority 2)
      URL: https://www.bis.gov.in/PDF/bs/BIS(Powers&Duties)Regulations_05092018.pdf
      Save as: `data/manual/law/dg_powers_regs.pdf`
- [ ] DoCA notification on precious metal articles (priority 2)
      URL: https://www.bis.gov.in/PDF/bs/DoCA_BIS_Hallmarking_Regulations_2018_Gazette_notification.pdf
      Save as: `data/manual/hallmarking_consumer/hm_doca_notification.pdf`

Also failed on retry (server error 504), low priority: `qco_199241`
(https://indiacode.nic.in/bitstream/123456789/1958/1/199241.pdf) → `data/manual/product_qco/qco_199241.pdf`

## Suggested extra documents (found on bis.gov.in, already added and downloaded)

These official guidelines are linked from the *Product Certification Process* page and fill the gaps you listed.
They are now in `data/sources.yaml` (category `certification`, priority 1):

| Topic | Document |
|---|---|
| Documents for an ISI application | Check-list for application (`application_checklist`) |
| Step-by-step grant of licence, option 1 / option 2, timelines, rejection | Guidelines for Grant of Licence, 25 Feb 2026 (`guide_grant_of_licence`) |
| Renewal of licence and its fees | Guidelines for Renewal of Licence (`guide_renewal`) |
| Change in licence details, additional varieties | Guidelines for Change in Scope of Licence (`guide_change_in_scope`) |
| Suspension and cancellation | Guidelines for Product Non-Conformity; Unsatisfactory Performance (`guide_non_conformity`, `guide_unsatisfactory_performance`) |
| Surveillance, retesting | Factory / Market Surveillance, Retesting of samples |
| MSME shared labs | Cluster Based Test Facility (CBTF) guidelines |
| Scheme IV | Grant / Renewal of Certificate of Conformity, CoC surveillance |

Still worth adding (linked from the FMCS and fee pages; not yet in `sources.yaml`):
- FMCS document check-list: https://www.bis.gov.in/wp-content/uploads/2018/08/FM_CHECKLIST.pdf
- FMCS fee list: https://www.bis.gov.in/wp-content/uploads/2021/06/LIST-OF-FEE-3.pdf
- Marking fee for all Scheme-I products: https://www.bis.gov.in/wp-content/uploads/2026/09/Marking-fee-for-all-products-under-certification-scheme-1.pdf
