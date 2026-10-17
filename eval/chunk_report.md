# Chunk report

**3624 chunks** from 551 sources: 997 product-table rows, 1681 from 502 QCO PDFs, 946 from 48 other documents.

## Chunk settings actually used (scripts/chunk.py)

- Split first on structure: top containers (`TOP`: Schedule / Chapter / Annex / Form), `Scheme-I…X` headings, numbered items with a real title (`17. Prohibition…`), markdown headings and FAQ questions. Acts are also split at every sub-section `(1)`, `(2)`… (`Section 29(3)` is its own chunk).
- Then cap each chunk at **800 tokens** with **100 tokens overlap** (tiktoken cl100k); pieces under **120 tokens** (25 for Acts) are merged into the next one.
- Fragments with fewer than 40 letters are dropped; every product-table row is one chunk.

## Size (characters)

min 63 · avg 1323 · median 1014 · max 4076

### Under 100 characters (6)

- `cert_apply_online::0000` (70): # Apply Online * [Click here to Apply Online](http://manakonline.in/)
- `hm_regulations_2018::0050` (86): # Substituted vide Gazette notification No. F. No. BS/11/05/2018 dated 12 October 2018
- `bis_act_2016::0010` (92): (9) "consumer" means a person as defined in the Consumer Protection Act, 1986; [68 of 1986.]
- `bis_act_2016::0014` (98): (15) "Governing Council" means a Governing Council constituted under sub-section (3) of section 3;
- `ca_amdt_2026::0055` (63): 3. Other terms and conditions of the licence shall remain same.
- `ca_regulations_2018::0219` (86): # Substituted vide Gazette notification No. F. No. BS/11/11/2018 dated 12 October 2018

### Over 3,000 characters (423)

- `cert_faq::0000` (3839) Frequently Asked Questions
- `cert_faq::0001` (3654) Frequently Asked Questions
- `cert_faq::0002` (4010) Frequently Asked Questions
- `hm_overview::0000` (3462) Hallmarking overview
- `guide_additional_scheme1::0003` (3264) 1. General Principles
- `guide_additional_scheme1::0004` (3721) 2. Submission of Application
- `guide_additional_scheme1::0006` (3120) 3. Factory Inspection
- `guide_additional_scheme1::0007` (3516) 4. Sample collection and testing
- `guide_additional_scheme1::0014` (3483) 10. Handholding and Professional Support to MSMEs
- `guide_cbtf_msme::0012` (3984) Annexure-III > 4. Guidelines
- `guide_cbtf_msme::0013` (3394) Annexure-III > 4. Guidelines
- `guide_change_in_scope::0001` (3732) 1. General Principles for CSoL
- `guide_coc_surveillance::0000` (3480) 
- `guide_coc_surveillance::0001` (4076) 
- `guide_coc_surveillance::0002` (3496) 
- `guide_coc_surveillance::0003` (3149) 
- `guide_coc_surveillance::0004` (3643) 
- `guide_coc_surveillance::0005` (3698) 
- `guide_coc_surveillance::0006` (3475) 
- `guide_coc_surveillance::0007` (3625) 
- `guide_factory_surveillance::0000` (3788) 
- `guide_factory_surveillance::0001` (3963) 
- `guide_factory_surveillance::0002` (3753) 
- `guide_factory_surveillance::0004` (4035) Annexure-I
- `guide_factory_surveillance::0009` (3889) Annexure-I > 7. Verification of Details regarding Manufacturing Proces
- `guide_factory_surveillance::0010` (3783) Annexure-I > 7. Verification of Details regarding Manufacturing Proces
- `guide_factory_surveillance::0011` (3571) Annexure-I > 7. Verification of Details regarding Manufacturing Proces
- `guide_factory_surveillance::0012` (4000) Annexure-I > 9. Laboratory and Inspection
- `guide_factory_surveillance::0013` (4009) Annexure-I > 9. Laboratory and Inspection
- `guide_factory_surveillance::0019` (3914) Annexure-I > 15. ISS Specific field’s verification: This section is un
- `guide_factory_surveillance::0020` (3390) Annexure-II
- `guide_grant_coc::0033` (3648) Annexure – IX > 7. We ................................
- `guide_grant_coc::0034` (3397) Annexure-XI
- `guide_grant_coc::0036` (3778) Annexure-XI > 3. Nomination
- `guide_grant_of_licence::0004` (3696) Annexure-II(C)
- `guide_grant_of_licence::0005` (3775) Annexure-II(C)
- `guide_grant_of_licence::0008` (3447) Annexure-I
- `guide_grant_of_licence::0010` (3183) Annexure-I > 6.
- `guide_grant_of_licence::0011` (3382) Annexure-I > 8.
- `guide_grant_of_licence::0023` (3007) Annexure-II (B) > Scheme-I

## Chunks per doc_type

| doc_type | chunks |
|---|---|
| qco | 2678 |
| guideline | 351 |
| regulation | 336 |
| act | 149 |
| page | 32 |
| faq | 32 |
| rule | 28 |
| order | 18 |

## Chunks per scheme

| scheme | chunks |
|---|---|
| I | 2909 |
| general | 258 |
| II | 219 |
| Hallmarking | 106 |
| IV | 80 |
| III | 19 |
| FMCS | 14 |
| VII | 8 |
| VI | 7 |
| V | 4 |

## Chunks per source (all)

| source_id | chunks | title |
|---|---|---|
| scheme1_products_table | 803 | Scheme I (ISI mark): products under compulsory certification |
| ca_regulations_2018 | 220 | BIS (Conformity Assessment) Regulations, 2018 |
| bis_act_2016 | 149 | Bureau of Indian Standards Act, 2016 |
| upcoming_qcos | 121 | Upcoming QCOs notified and due for implementation |
| qco_s_o_1081_e | 114 | S.O 1081 (E) |
| scheme2_page | 76 | Scheme II (CRS registration) page |
| guide_grant_of_licence | 67 | Guidelines for Grant of Licence (Scheme I, 25 Feb 2026) |
| ca_amdt_2026 | 59 | CA Amendment Regulations, 2026 |
| hm_regulations_2018 | 51 | BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1) |
| guide_grant_coc | 44 | Guidelines for Grant of Certificate of Conformity (Scheme IV) |
| guide_non_conformity | 42 | Guidelines for Dealing with Product Non-Conformity (25 Feb 2026) |
| simplified_procedure_list | 33 | List of Products under Simplified Procedure |
| qco_qco_on_144_steel_steel_products_1 | 32 | Act) and in the supersession of the Steel and Steel Products (Quality  |
| qco_145_qco_order | 29 | 145 QCO Order |
| qco_14_qcos_for_chemical_products | 29 | This order may be called the Pyridine (Quality Control) Order, 2020 (1 |
| bis_rules_2018 | 28 | BIS Rules, 2018 (with all amendments) |
| guide_unsatisfactory_performance | 27 | Guidelines for Dealing with Unsatisfactory Performance (25 Feb 2026) |
| qco_amended_quality_control_order_for_various_chemicals | 25 | Amended Quality Control Order for various chemicals |
| qco_steel_steel_product_qco_2024 | 24 | Steel Steel Product QCO 2024 |
| qco_cctv_camera_cro_2021 | 23 | CCTV Camera CRO 2021 |
| guide_factory_surveillance | 21 | Guidelines for Factory Surveillance (25 Feb 2026) |
| qco_steel_and_steel_products_qco_2024 | 20 | Steel and Steel Products QCO 2024 |
| qco_steel_qco_dated_17_july_2020_with_corrigendum | 20 | Steel QCO dated 17 July 2020 with corrigendum |
| qco_notification_for_08_qcos_from_dcpc_27042022_47ded9 | 17 | 1,3 Phenylenediamine (Quality Control) Order, 2022 (S.O. 1960(E), date |
| qco_notification_for_08_qcos_from_dcpc_27042022_4b4459 | 17 | Notification for 08 QCOs from DCPC 27042022 |
| guide_additional_scheme1 | 16 | Additional Guidelines for Scheme-I (DG Order No. 3 of 2020) |
| guide_cbtf_msme | 15 | Guidelines for utilisation of Cluster Based Test Facility (CBTF) by MS |
| hm_order_june_2021 | 15 | Hallmarking Order, June 2021 |
| qco_polyester_qco | 15 | This order may be called the Polyester Continuous Filament Fully Drawn |
| qco_chemical_products_quality_control_order_2021_3 | 13 | Chemical Products Quality Control Order 2021 3 |
| qco_steel_qco_2020_dated_27th_may_2020 | 13 | Steel QCO 2020 dated 27th May 2020 |
| guide_change_in_scope | 12 | Guidelines for Change in Scope of Licence |
| guide_market_surveillance | 12 | Guidelines for Market Surveillance (25 Feb 2026) |
| guide_renewal | 12 | Guidelines for Renewal of Licence |
| hm_jewellers_guidelines | 12 | Guidelines for Jewellers (Jul 2026) |
| hm_faq_general | 11 | Hallmarking FAQ (general) |
| qco_date_of_extn_of_qco_of_12_gazette_evapepolyester_yarnslab | 11 | Date of Extn. of QCO of 12 gazette EVAPEPolyester yarnsLAB |
| qco_fssai_regulation_2011 | 11 | Food Safety & Standards (FSSAI Regulation 2011) |
| qco_qco_for_ethylene_glycol_phthalic_anhydride_toluene_terephthalic_acid_n_butyl_acrylate | 11 | QCO for ethylene glycol phthalic anhydride Toluene Terephthalic acid n |
| qco_steel_qco_14022020_1 | 11 | Steel QCO 14022020 1 |
| guide_renewal_coc | 10 | Guidelines for Renewal of Certificate of Conformity (Scheme IV) |
| qco_quality_control_orders_for_chemicals | 10 | Quality Control Orders for Chemicals |
| fmcs_faq | 9 | FMCS FAQs |
| guide_coc_surveillance | 9 | Guidelines for Surveillance under Scheme IV (Stampings/Laminations/Cor |
| qco_amendments_in_quality_control_order | 9 | Amendments in Quality Control Order |
| qco_amendments_in_quality_control_order_2 | 9 | Amendments in Quality Control Order 2 |
| qco_extension_of_date_of_implementation_of_04_petrochemicals_2 | 9 | Extension of Date of implementation of 04 Petrochemicals 2 |
| qco_goods_articles_exemption_order_against_import_order_2468af | 9 | Goods Articles Exemption Order against Import Order |
| qco_goods_articles_exemption_order_against_import_order_3fcf18 | 9 | Goods Articles Exemption Order against Import Order |
| application_checklist | 8 | Check-list for application to be submitted by applicant to BIS |
| crs_standard_mark_guidelines | 8 | CRS Standard Mark Guidelines |
| qco_guidance | 8 | Guidance Document on Quality Control Orders |
| qco_3_n_n_di_ethyl_aminophenol_quality_control_order_2021 | 7 | 3 (N, N Di-Ethyl) Aminophenol (Quality Control) Order, 2021 (S.O. No.  |
| qco_chemical_products_amendment_order | 7 | Chemical products amendment order |
| qco_extension_of_date_of_implementation_of_06_petrochemicals | 7 | Extension of Date of implementation of 06 Petrochemicals |
| qco_extension_of_polyester_yarn_qcos17072023 | 7 | Extension of Polyester Yarn QCOs17072023 |
| qco_extension_order_of_06_petrochemicals_31032023 | 7 | Extension order of 06 petrochemicals 31032023 |
| qco_methylene_chloride_dichloromethane_quality_control_order_2021_1 | 7 | Methylene Chloride Dichloromethane Quality Control Order 2021 1 |
| qco_mnre_qco_solar_pv_products_standards_essentialrequirements | 7 | MNRE QCO Solar PV Products Standards EssentialRequirements |
| qco_red_phosphorus_quality_control_order_2021_1 | 7 | Red Phosphorus (Quality Control) Order, 2021 (S.O. No. 2033 (E) 25/05/ |
| law_page | 6 | BIS Act, Rules & Regulations index page |
| qco_amendment_order_of_ethylene_dichloride_polycarbonatevinyl_chloride_monomer_p_xylene_and_polyurethanes | 6 | Amendment order of Ethylene Dichloride PolycarbonateVinyl Chloride Mon |
| qco_amendment_orders_for_various_chemical_products | 6 | Amendment Orders for various chemical Products |
| qco_ethylene_glycol_quality_control_amendment_order_2020 | 6 | Ethylene Glycol Quality Control Amendment Order 2020 |
| qco_gazette_so2920_e | 6 | Bureau of Indian Standards Rules, 1987 (Gazette SO2920 E) |
| qco_notification_of_transition_facilitation_quality_control_order_2026 | 6 | Notification of Transition Facilitation Quality Control Order 2026 |
| qco_notification_of_transition_facilitation_quality_control_order_2026_1 | 6 | Notification of Transition Facilitation Quality Control Order 2026 1 |
| qco_pvc_homopolymers_pp_materials_for_moulding_and_extrusion_and_diesel_engine_nox_reduction_agent_aus_32_qco | 6 | PVC Homopolymers PP Materials for Moulding and Extrusion and Diesel En |
| qco_qco_amendment_order14062022 | 6 | Order to amend the Toluene (Quality Control) Order, 2021 (QCO amendmen |
| qco_safety_of_household_commercial_and_similar_electrical_appliances_qco_2024 | 6 | Safety of Household Commercial and Similar Electrical Appliances QCO 2 |
| qco_amendment_order_of_4_dcpc_products | 5 | Amendment order of 4 DCPC products |
| qco_amendment_order_of_various_chemicals_dated_10_march_2022 | 5 | Amendment order of various chemicals dated 10 March 2022 |
| qco_bolts_nuts_and_fateners_qco_2024 | 5 | Bolts, Nuts and Fasteners (Quality Control) Order, 2023 (Bolts Nuts an |
| qco_cross_recessed_screws_quality_control_order2024 | 5 | Cross Recessed Screws Quality Control Order2024 |
| qco_cross_recessed_screws_quality_control_order_2025 | 5 | Cross Recessed Screws Quality Control Order 2025 |
| qco_environment_protection_115_amendment_rules_2021 | 5 | Environment Protection 115 Amendment Rules 2021 |
| qco_extension_in_date_of_implementation_of_03_petrochemicals | 5 | Extension in date of implementation of 03 Petrochemicals |
| qco_gazette_notification_for_extension_of_qco_for_10_chemicals | 5 | Gazette Notification for extension of QCO for 10 Chemicals |
| qco_gazette_notification_for_extension_of_qco_of_10_chemicals | 5 | Gazette Notification for extension of QCO of 10 Chemicals |
| qco_polyethylene_woven_sacks_qco | 5 | High Density Polyethylene (HDPE) /Polypropylene (PP) Woven Sacks for P |
| qco_qco_for_ethyl_acrylate_methyl_acrylate_and_vinyl_acetate_monomer | 5 | QCO for ethyl acrylate methyl acrylate and Vinyl acetate monomer |
| qco_safety_of_household_commercial_and_similar_electrical_appliances_quality_control_order_2026 | 5 | Safety of Household Commercial and Similar Electrical Appliances Quali |
| qco_so_1121_1123_qco_extension_order_dcpc_10032023 | 5 | Order further to amend the Acrylonitrile - Butadiene Styrene (ABS) (Qu |
| qco_textiles_high_density_polyethylene_hdpepolypropylenepp_woven_sacks_amendment_order2024 | 5 | Textiles—High Density Polyethylene HDPEPolypropylenePP Woven sacks Ame |
| cert_faq | 4 | Product Certification FAQ |
| consumer_protection | 4 | Consumer protection |
| hm_faq_general__bis_act_and_regulation_faq | 4 | Hallmarking FAQ (general): BIS Act and Regulation |
| hm_faq_general__mandatory | 4 | Hallmarking FAQ (general): Consumers |
| qco_3_different_types_of_woven_sacks_qco_2024 | 4 | 3 different types of Woven sacks QCO 2024 |
| qco_516_e | 4 | SO 516(E), dated 25th May 1987 (516 E) |
| qco_air_conditioner_and_its_related_parts | 4 | Air Conditioner and its related parts |
| qco_amendment_in_06_chemical_qco | 4 | Lauric Acid (Quality Control) Order, 2022 (Amendment in 06 Chemical QC |
| qco_amendment_order_of_lauric_acid_acid_oil_palm_fatty_acid_rice_bran_fatty_acidcoconut_fatty_acid_and_hydrogenated_rice_bran_fatty_acids | 4 | Amendment order of Lauric acid Acid oil Palm fatty acid Rice bran fatt |
| qco_bicycles_retro_reflective_devices_quality_control_order_2021 | 4 | Bicycles Retro Reflective Devices Quality Control Order 2021 |
| qco_cookwareand_utensils_qco_2023 | 4 | This Order may be called the Cookware and Utensils (Quality Control) O |
| qco_domestic_gas_stoves_for_use_with_png_qco_2023 | 4 | Domestic Gas Stoves for use with PNG QCO 2023 |
| qco_electric_ceiling_type_fans_qco_2023 | 4 | Electric Ceiling Type Fans QCO 2023 |
| qco_ethylene_dichloride_vinyl_chloride_monomer_polycarbonate_qco_amendments | 4 | Ethylene Dichloride Vinyl Chloride Monomer polycarbonate QCO Amendment |
| qco_extension_of_wood_based_products_qco | 4 | Extension of Wood Based Products QCO |
| qco_fire_extinguisher_qco_2023 | 4 | This Order may be called the Fire Extinguishers (Quality Control) Orde |
| qco_footwear_made_from_all_rubber_and_all_polymeric_materials_and_its_components_qco_2024 | 4 | Footwear made from All Rubber and all Polymeric Materials and its Comp |
| qco_gazette_notification_for_extension_of_qco_for_7_chemicals | 4 | Gazette Notification for extension of QCO for 7 Chemicals |
| qco_insulated_flask_bottles_and_containers_for_domestic_use_qco | 4 | Insulated Flask Bottles and Containers for Domestic Use QCO |
| qco_meity_qco_for_additional_12_products | 4 | MeitY QCO for additional 12 products |
| qco_notified_plywood_and_wooden_flush_door_shutters_quality_control_order_2023_in_e_gazette | 4 | Notified Plywood and Wooden flush door shutters Quality Control Order  |
| qco_potable_water_bottles_quality_controlorder_2024 | 4 | Potable Water Bottles Quality ControlOrder 2024 |
| qco_qco_amendment_order_for_acrylonitrile_malaeic_anhydried_styrene_vinyl_benzene | 4 | QCO amendment order for Acrylonitrile Malaeic anhydried Styrene Vinyl  |
| qco_qco_coc_bycycle_dpiit | 4 | This Order may be called the Bicycles- Retro Reflective Devices (Quali |
| qco_qco_dated_10th_oct2018 | 4 | Bureau of Indian Standards Kitchen Appliances (Quality Control) Order, |
| qco_quality_control_order_of_03_chemicals_viz_i_h_acid_ii_k_acid_iii_vinyl_sulphone | 4 | Quality Control Order of 03 Chemicals viz. i H Acid ii K Acid iii Viny |
| qco_quality_control_orders_for_maleic_anhydride_acrylonitrile_and_styrene_vinyl_benzene_amendment | 4 | Quality Control Orders for Maleic Anhydride Acrylonitrile and Styrene  |
| qco_resin_treated_compressed_wood_laminates_qco_2024 | 4 | Resin Treated Compressed Wood Laminates QCO 2024 |
| qco_textiles_high_density_polyethylene_hdpe_polypropylene_pp_woven_sacks_for_packaging_of_50_kg_cement_quality_control_amendment_order_2025 | 4 | Textiles High Density Polyethylene Hdpe Polypropylene Pp Woven Sacks F |
| qco_textiles_high_density_polyethylene_hdpe_polypropylene_pp_woven_sacks_for_packaging_of_50_kg_cement_quality_control_amendment_order_2026 | 4 | Textiles High Density Polyethylene HDPE Polypropylene PP Woven Sacks f |
| qco_textiles_high_density_polyethylene_hdpe_polypropylene_pp_woven_sacks_for_packaging_of_50_kg_cement_quality_control_order_2025 | 4 | Textiles — High Density Polyethylene HDPE Polypropylene PP Woven Sacks |
| qco_textiles_polypropylene_pp_high_density_polyethylene_hdpe_laminated_woven_sacks_for_mail_sorting_storage_transport_and_distribution_quality_control | 4 | Textiles Polypropylene Pp High Density Polyethylene Hdpe Laminated Wov |
| qco_textiles_polypropylene_pp_high_density_polyethylene_hdpe_laminated_woven_sacks_for_mail_sorting_storage_transport_and_distribution_quality_control_amendment_order_2026 | 4 | Textiles Polypropylene PP High Density Polyethylene HDPE Laminated Wov |
| qco_textiles_polypropylene_pp_woven_laminated_block_bottom_valve_sacks_for_packaging_50_kg_cement_quality_control_amendment_order_2025 | 4 | Textiles —Polypropylene Pp Woven Laminated Block Bottom Valve Sacks Fo |
| qco_textiles_polypropylene_pp_woven_laminated_block_bottom_valve_sacks_for_packaging_50_kg_cement_quality_control_amendment_order_2026 | 4 | Textiles Polypropylene PP Woven Laminated Block Bottom Valve Sacks for |
| qco_textiles_polypropylene_pp_woven_laminated_block_bottom_valve_sacks_for_packaging_of_50_kg_cement_quality_control_order_2025 | 4 | Textiles — Polypropylene PP Woven Laminated Block Bottom Valve Sacks f |
| qco_textiles_polypropylene_pphigh_density_polyethylene_hdpe_laminated_woven_sacks_for_mail_sorting_storage_transport_and_distribution_quality_control_amendment_order_2025 | 4 | Textiles — Polypropylene PPHigh Density Polyethylene HDPE Laminated Wo |
| qco_textiles_woven_sacks_qco | 4 | Cement (Quality Control) Order, 2023 (Textiles Woven sacks QCO) |
| qco_water_purification_system_regulation_of_userules_2023_amendment | 4 | Water purification System Regulation of UseRules 2023 Amendment |
| qco_welding_rod_electrode_qco | 4 | This Order may be called The Welding Rods and Electrodes (Quality Cont |
| cert_fee | 3 | Product Certification Fee |
| hm_overview | 3 | Hallmarking overview |
| guide_retesting | 3 | Guidelines for Sample Coding and Retesting of Samples |
| marking_requirements | 3 | Marking requirement as per BIS (CA) Regulations |
| qco_100_percent_polyester_spun_grey_and_white_yarn_rescind_order_2025 | 3 | 100 Percent Polyester Spun Grey and White Yarn Rescind Order 2025 |
| qco_184588 | 3 | 184588 |
| qco_2742 | 3 | Bureau of Indian Standards Rules, 1987 (2742) |
| qco_acid_oil_quality_control_amendment_order_2025 | 3 | Acid Oil Quality Control Amendment Order 2025 |
| qco_acitic_acid | 3 | This Order may be called the Acetic Acid (Quality Control) Order, 2019 |
| qco_acrylonitrile_butadiene_styrene_abs_rescind_order_2025 | 3 | Acrylonitrile Butadiene Styrene ABS Rescind Order 2025 |
| qco_acrylonitrile_qco_1 | 3 | This order may be called the Acrylonitrile (Quality Control) Order, 20 |
| qco_air_conditioner_and_its_related_parts_hermetic_compressor_and_temperature_sensing_controls_quality_control_second_amendment_order_2020 | 3 | Air Conditioner and its related Parts Hermetic Compressor and Temperat |
| qco_air_cooler_and_air_filters_quality_control_2025 | 3 | Air Cooler and Air Filters Quality Control 2025 |
| qco_al_and_al_alloys_qco_2024 | 3 | Aluminium and Aluminium Alloy Products (Quality Control) Order, 2023 ( |
| qco_aluminium_aluminium_alloy_products_quality_control_order_2026 | 3 | Aluminium Aluminium Alloy Products Quality Control Order 2026 |
| qco_aluminium_foil_qco | 3 | Aluminium Foil (Quality Control) Order, 2020 (S.O. 687 (E) dated 13/02 |
| qco_aluminum_and_aluminum_alloy_products_qco | 3 | Aluminum and Aluminum alloy products QCO |
| qco_amendment_in_quality_control_order_of_06_chemicals | 3 | Amendment in Quality Control Order of 06 Chemicals |
| qco_amendment_order_of_various_chemicals_dated_11_march_2022 | 3 | Amendment order of various chemicals dated 11 March 2022 |
| qco_asbestos_or_fibre_cement_based_products_qco_2024 | 3 | Asbestos or Fibre Cement based products QCO 2024 |
| qco_boricacidqualitycontrolorder_1 | 3 | BoricAcidQualityControlOrder 1 |
| qco_bottled_water_dispenser_qco_2023 | 3 | This Order may be called the Bottled water dispensers (Quality Control |
| qco_bottled_water_dispensers_quality_controlorder2024 | 3 | Bottled Water Dispensers Quality ControlOrder2024 |
| qco_butterfly_valve_qco | 3 | Butterfly valves (Quality Control) Order, 2020. (S.O. 1920 (E) dated 1 |
| qco_cables_28012020 | 3 | Cables (Quality Control) Order, 2020 (S.O. 280 (E) dated 21/01/2020 )  |
| qco_cast_iron_products | 3 | Cast Iron Products (Quality Control) Order, 2023 (Cast Iron Products) |
| qco_cast_iron_products_qco_2023 | 3 | This order may be called the Cast Iron Products (Quality Control) Orde |
| qco_centrifugally_cast_spun_iron_pipes_quality_control_order_2021 | 3 | Centrifugally Cast Spun Iron Pipes Quality Control Order 2021 |
| qco_coconut_fatty_acids_quality_control_amendment_order_2025 | 3 | Coconut Fatty Acids Quality Control Amendment Order 2025 |
| qco_cookware_utensils_and_cans_for_food_and_beverages_qco_2024 | 3 | Cookware Utensils and cans for food and beverages QCO 2024 |
| qco_cookware_utensils_and_cans_for_food_and_beverages_qco_2024_1 | 3 | Cookware Utensils and cans for food and beverages QCO 2024 1 |
| qco_cookware_utensils_and_cans_for_foods_and_baverages_qco_2025 | 3 | Cookware Utensils and Cans for Foods and Baverages QCO 2025 |
| qco_cookware_utensils_and_cans_for_foods_and_beverages_quality_control_order_2026_0c8a39 | 3 | Cookware Utensils and Cans for Foods and Beverages Quality Control Ord |
| qco_cookware_utensils_and_cans_for_foods_and_beverages_quality_control_order_2026_6f5030 | 3 | Cookware Utensils and Cans for Foods and Beverages Quality Control Ord |
| qco_copper_products_qco_2023 | 3 | This order may be called the Copper Products (Quality Control) Order,  |
| qco_copper_products_quality_control_2024 | 3 | Copper Products Quality Control 2024 |
| qco_copper_qco_2023 | 3 | This Order may be called the Copper (Quality Control) Order, 2023 (Cop |
| qco_cycle_and_rickshaw_tyres_and_tubes | 3 | Cycle and Rickshaw tyres and Tubes |
| qco_dcpc_4_products_02022024 | 3 | Central Government hereby makes the following amendment in the Morphol |
| qco_dcpc_extn_of_06_chemicals | 3 | Central Government hereby makes the following amendment in the Pyridin |
| qco_domestic_pressure_cooker_qco_2020_1 | 3 | (Quality Control) Order, 2020 (S.O. 294 (E) dated 21/01/2020) Domestic |
| qco_door_fittings_qco_2023 | 3 | This order may be called Door Fittings (Quality Control) Order, 2023 ( |
| qco_drinking_water_cooler_qco | 3 | This Order may be called the Self- Contained Drinking Water Cooler (Qu |
| qco_drums_tins_qco_2023 | 3 | This Order may be called the Drums and Tins (Quality Control) Order, 2 |
| qco_electric_fence_energizer_qco_2024 | 3 | This Order may be called the Electric Fence Energizers (Quality Contro |
| qco_electrical_appliance_fans_qco_2023 | 3 | Electrical appliance fans QCO 2023 |
| qco_electrical_appliance_for_commercial_dispensing_and_vending_qco_2023 | 3 | Electrical appliance for commercial dispensing and vending QCO 2023 |
| qco_electrical_appliance_for_domestic_clothes_washing_qco_2023 | 3 | Electrical appliance for domestic clothes washing QCO 2023 |
| qco_electrical_appliance_for_domestic_clothes_washing_qco_2024 | 3 | Electrical appliance for domestic clothes washing QCO 2024 |
| qco_electrical_appliances_for_commercial_dispensing_and_vending_qco_2024 | 3 | Electrical Appliances for Commercial Dispensing and Vending QCO 2024 |
| qco_electrical_appliances_for_commercial_dispensing_and_vending_qco_2025 | 3 | Electrical Appliances for Commercial Dispensing and Vending QCO 2025 |
| qco_electrical_appliances_for_domestic_water_heating_qco_2025 | 3 | Electrical Appliances for domestic water heating QCO 2025 |
| qco_electrical_appliances_for_domestic_water_heating_quality_control_order_2023 | 3 | Electrical Appliances for domestic water heating Quality Control Order |
| qco_electrical_appliances_for_kitchen_qco_2023 | 3 | Electrical Appliances for Kitchen QCO 2023 |
| qco_electrical_appliances_for_skin_or_hair_care_qco_2023 | 3 | Electrical Appliances for Skin or Hair care QCO 2023 |
| qco_ethylene_dichloride_vinyl_chloride_monomer_qco | 3 | Ethylene Dichloride Vinyl Chloride Monomer QCO |
| qco_ethylene_glycol_qco_extension_order28122022 | 3 | Ethylene glycol QCO extension order28122022 |
| qco_ethylene_glycol_rescind_order_2025 | 3 | Ethylene Glycol Rescind Order 2025 |
| qco_ethylene_vinyl_acetate_eva_copolymers_rescind_order_2025 | 3 | Ethylene Vinyl Acetate EVA Copolymers Rescind Order 2025 |
| qco_eva_coplymer_qco | 3 | This order may be called the Ethylene Vinyl Acetate Copolymers (Qualit |
| qco_extension_for_date_of_implementation_of_06_qcos | 3 | Extension for date of implementation of 06 QCOs |
| qco_extension_of_doi_of_bicycles_retro_reflective_devices_quality_control_order_2021 | 3 | Extension of DOI of Bicycles Retro Reflective Devices Quality Control  |
| qco_flashlight_quality_control_order_2025 | 3 | Flashlight Quality Control Order 2025 |
| qco_flat_transparent_sheet_glass_qco | 3 | Flat Transparent Sheet Glass QCO |
| qco_flat_transparent_sheet_glass_quality_control_order_2021 | 3 | Flat Transparent Sheet Glass Quality Control Order 2021 |
| qco_flux_cored_tubular_electrodes_quality_control_order_2021 | 3 | Flux Cored Tubular Electrodes Quality Control Order 2021 |
| qco_footwear_made_from_leather_and_other_materials_qco_2024 | 3 | Footwear made from Leather and other Materials QCO 2024 |
| qco_footwear_qualitycontrolorder_2020_29october2020 | 3 | Footwear QualityControlOrder 2020 29October2020 |
| qco_footwearleather_qualitycontrolorder_2020_29october2020 | 3 | FootwearLeather QualityControlOrder 2020 29October2020 |
| qco_furniture_qco_17_02_2025 | 3 | This order may be called the Furniture (Quality Control) Order, 2025 ( |
| qco_gas_cylinder_amendment_rules_2026 | 3 | WHEREAS the draft of certain rules further to amend the Gas Cylinders  |
| qco_gas_cylinder_second_amendment_rules_05062026 | 3 | Gas Cylinder Second Amendment Rules 05062026 |
| qco_gazette_notification_prohibition_02_09_2022 | 3 | Gazette Notification Prohibition 02 09 2022 |
| qco_gazette_notification_quality_control_order_2183_30052018 | 3 | Gazette notification quality control order 2183 30052018 |
| qco_goods_articles_exemption_order_against_purchase_order_1d612d | 3 | Goods Articles Exemption Order against Purchase Order |
| qco_goods_articles_exemption_order_against_purchase_order_b5b2ff | 3 | Goods Articles Exemption Order against Purchase Order |
| qco_gypsum_based_building_materials_qco_2024 | 3 | Gypsum based Building Materials QCO 2024 |
| qco_hand_tools_quality_control_order_2025 | 3 | Hand Tools Quality Control Order 2025 |
| qco_hand_tools_quality_control_order_2025_1 | 3 | Hand Tools Quality Control Order 2025 1 |
| qco_helmet_for_police_force_civil_defence_personal_protection_qco_2023 | 3 | Helmet for Police Force Civil Defence Personal Protection QCO 2023 |
| qco_hinges_qco | 3 | This order may be called the Hinges (Quality Control) Order, 2023 (Hin |
| qco_hinges_qco_pdf_26_july | 3 | Hinges (Quality Control) Order, 2023 (Hinges QCO.pdf 26 July) |
| qco_hinges_quality_control_order_2025 | 3 | Hinges (Quality Control) Order, 2024 (Hinges Quality Control Order 202 |
| qco_household_zig_zag_sewing_machine | 3 | Household Zig Zag Sewing Machine |
| qco_hydrogenated_rice_bran_fatty_acids_quality_control_amendment_order_2025 | 3 | Hydrogenated Rice Bran Fatty Acids Quality Control Amendment Order 202 |
| qco_lauric_acid_quality_control_amendment_order_2025 | 3 | Lauric Acid Quality Control Amendment Order 2025 |
| qco_leather_footwear_qco_2022 | 3 | This Order may be called the Footwear Made from allRubber and all Poly |
| qco_legal_metrology_material_measures_of_length_qco_2023 | 3 | Legal Metrology Material Measures of Length QCO 2023 |
| qco_linear_alkyl_benzene_qco | 3 | This order may be called the Linear Alkyl Benzene (Quality Control) Or |
| qco_methyl_acrylate_ethyl_acrylate_quality_control_amendment_order_2025 | 3 | Methyl Acrylate Ethyl Acrylate Quality Control Amendment Order 2025 |
| qco_methyl_ethyl_n_butyl_acrylate_qco | 3 | Methyl Ethyl n Butyl Acrylate QCO |
| qco_n_butyl_acrylate_qco | 3 | This order may be called the n-Butyl Acrylate (Quality Control) Order, |
| qco_ortho_phosphoric_acid_quality_control_order_2021_1 | 3 | Ortho Phosphoric Acid Quality Control Order 2021 1 |
| qco_p_xylene_and_polyurethanes_qco_2024 | 3 | p Xylene and Polyurethanes QCO 2024 |
| qco_p_xylene_polyurethanes_qco_amendment_2025 | 3 | p Xylene Polyurethanes QCO Amendment 2025 |
| qco_palm_fatty_acids_quality_control_amendment_order_2025 | 3 | Palm Fatty Acids Quality Control Amendment Order 2025 |
| qco_personalprotective_footwearqualitycontrolorder2020_29october2020 | 3 | PersonalProtective FootwearQualityControlOrder2020 29October2020 |
| qco_phthallic_anhydride_qco | 3 | This order may be called the Phthalic Anhydride (Quality Control) Orde |
| qco_plug_and_socket_qco | 3 | Plugs and Socket-Outlets and Alternating Current Direct Connected Stat |
| qco_plugs_and_socket_outlets_and_ac_direct_connected_static_prepayment_meters_for_active_energy_quality_control_order_2021 | 3 | Plugs and Socket Outlets and AC Direct Connected Static Prepayment Met |
| qco_plywood_and_wooden_flush_door_shutters_qco_2024 | 3 | Plywood and Wooden flush door shutters QCO 2024 |
| qco_poly_aluminium_chloride | 3 | This Order may be called the Poly Aluminium Chloride (Quality Control) |
| qco_polycarbonate_rescind_order_2025 | 3 | Polycarbonate Rescind Order 2025 |
| qco_polyester_continuous_filament_fully_drawn_yarn_rescind_order_2025 | 3 | Polyester Continuous Filament Fully Drawn Yarn Rescind Order 2025 |
| qco_polyester_industrial_yarn_idy_rescind_order_2025 | 3 | Polyester Industrial Yarn IDY Rescind Order 2025 |
| qco_polyester_partially_oriented_yarn_rescind_order_2025 | 3 | Polyester Partially Oriented Yarn Rescind Order 2025 |
| qco_polyester_staple_fibres_psf_rescind_order_2025 | 3 | Polyester Staple Fibres PSF Rescind Order 2025 |
| qco_polyethylene_material_for_moulding_and_extrusion_rescind_order_2025 | 3 | Polyethylene Material for Moulding and Extrusion Rescind Order 2025 |
| qco_polypropylene_pp_materials_for_moulding_and_extrusion_rescind_order_2025 | 3 | Polypropylene PP Materials for Moulding and Extrusion Rescind Order 20 |
| qco_polyurethanes_rescind_order_2025 | 3 | Polyurethanes Rescind Order 2025 |
| qco_polyvinyl_chloride_pvc_homopolymers_rescind_order_2025 | 3 | Polyvinyl Chloride PVC Homopolymers Rescind Order 2025 |
| qco_precision_roller_and_bush_chains_attachments_qco | 3 | Precision Roller and Bush Chains attachments QCO |
| qco_precision_roller_and_bush_chainsattachments_and_associated_chains_sprockets_qco_2024 | 3 | Precision Roller and Bush ChainsAttachments and Associated Chains Spro |
| qco_punch_qco | 3 | This Order may be called the Press Tool- Punches (Quality Control) Ord |
| qco_qco_copier_paper_dpiit | 3 | Plain Copier Paper (Quality Control) Order, 2020. (S.O. 2149(E) dated  |
| qco_qco_ether_dcpc | 3 | Ether (Quality Control) Order, 2020 (S.O. 2183(E) dated 29/06/2020) Et |
| qco_qco_ethylene_glycol_dcpc | 3 | This order may be called the n-Butyl Acrylate (Quality Control) Order, |
| qco_qco_extension_2_petrochemicals | 3 | QCO Extension 2 petrochemicals |
| qco_qco_extension_for_vinyl_acatate_monomer_methyl_acrylate_ethyl_acrylate | 3 | QCO Extension for Vinyl acatate Monomer Methyl Acrylate Ethyl Acrylate |
| qco_qco_for_flux_cored_solder_wire_2023 | 3 | This order may be called the Flux Cored Solder Wire (Quality Control)  |
| qco_qco_for_miscellaneous_steel_products | 3 | QCO for Miscellaneous Steel Products |
| qco_qco_lpg_stoves | 3 | Domestic Gas Stoves for use with Liquefied Petroleum Gases (Quality Co |
| qco_qco_on_polyphosphoric_acid | 3 | This Order may be called the Polyphosphoric Acid (Quality Control) Ord |
| qco_quality_control_order_for_abs_and_polyurethanes_amendment_compressed | 3 | Quality control order for ABS and Polyurethanes amendment compressed |
| qco_refined_nickel_quality_control_order_2025 | 3 | Refined Nickel Quality Control Order 2025 |
| qco_refrigerating_appliances_quality_control_amendemnt_order_2021 | 3 | Refrigerating Appliances Quality Control Amendemnt Order 2021 |
| qco_refrigerating_appliances_quality_control_order_2020 | 3 | Refrigerating Appliances Quality Control Order 2020 |
| qco_rice_bran_fatty_acids_quality_control_amendment_order_2025 | 3 | Rice Bran Fatty Acids Quality Control Amendment Order 2025 |
| qco_rubber_gaskets_for_pressure_cookers | 3 | Rubber Gaskets for Pressure Cookers |
| qco_rubber_hose_lpg_qco | 3 | Rubber Hose for Liquefied Petroleum Gas (LPG) (Quality Control ) Order |
| qco_rubber_polymeric_footwera_qco_2022 | 3 | Rubber Polymeric Footwera QCO 2022 |
| qco_safety_glass_qco | 3 | Safety Glass QCO |
| qco_safety_of_household_commercial_and_similar_electrical_appliances_quality_control_order_2025 | 3 | Safety of Household Commercial and Similar Electrical Appliances Quali |
| qco_self_contained_drinking_water_cooler_qco_2024 | 3 | Self Contained Drinking Water Cooler QCO 2024 |
| qco_smart_meter_qco | 3 | This Order may be called The Smart Meters (Quality Control) Order, 202 |
| qco_so_no_2604_e | 3 | Order further to amend the Electrical Wires, Cables, Appliances and Pr |
| qco_solar_dc_cable_and_fire_survival_cable_qco_2023 | 3 | Solar DC Cable and Fire Survival Cable QCO 2023 |
| qco_solar_thermal_systems_devices_and_components_qco_2024 | 3 | Solar Thermal Systems Devices and Components QCO 2024 |
| qco_stainless_steel_pipes_and_tubes_qco_2025 | 3 | Stainless Steel Pipes and Tubes QCO 2025 |
| qco_steel_wires_or_strands_nylon_or_wire_ropes_and_wire_mesh_qco_2024 | 3 | Steel Wires or Strands Nylon or Wire Ropes and wire mesh QCO 2024 |
| qco_steel_wires_or_strands_nylon_or_wire_ropes_qco_2023 | 3 | Steel Wires or Strands Nylon or Wire Ropes QCO 2023 |
| qco_styrine_qco | 3 | This order may be called the Styrene (Vinyl Benzene) (Quality Control) |
| qco_telescopic_ball_bearing_drawer_slide_quality_control_order_2024 | 3 | Telescopic Ball Bearing Drawer Slide Quality Control Order 2024 |
| qco_terephthalic_acid_rescid_order_2025 | 3 | Terephthalic Acid Rescid Order 2025 |
| qco_toluene_qco | 3 | This order may be called the Toluene (Quality Control) Order, 2020 (To |
| qco_toy_qc_order | 3 | This Order may be called the Toys (Quality Control) Order, 2020 (Toy Q |
| qco_transparent_float_glass_quality_control_order_2021 | 3 | Transparent Float Glass Quality Control Order 2021 |
| qco_trimethyl_phosphite_quality_control_order_2022 | 3 | Trimethyl Phosphite (Quality Control) Order, 2022 (S.O. 1637(E), dated |
| qco_v_belt_quality_control_order_2024 | 3 | This order may be called the V-Belt (Quality Control) Order, 2024 (V B |
| qco_vinyl_acetate_monomer | 3 | This order may be called the Vinyl Acetate Monomer (Quality Control) O |
| qco_vinyl_acetate_monomer_and_methyl_acrylate_ethyl_acrylate_quality_comtrol_orders | 3 | Vinyl Acetate Monomer and Methyl Acrylate Ethyl Acrylate Quality Comtr |
| qco_vinyl_acetate_monomer_quality_control_amendment_order_2025 | 3 | Vinyl Acetate Monomer Quality Control Amendment Order 2025 |
| qco_water_meters_and_accessories_qco_2023 | 3 | Water meters and accessories QCO 2023 |
| qco_wheel_rim_qco | 3 | This Order may be called the Automobile Wheel Rim Component (Quality C |
| qco_woven_sacks_qco | 3 | The Textiles-High Density Polyethylene and Polypropylene woven sacks f |
| cert_overview | 2 | Product Certification Overview |
| fmcs_how_to_apply | 2 | FMCS How to Apply |
| fmcs_overview | 2 | FMCS (Foreign Manufacturers) Overview |
| hm_mandatory_order_page | 2 | Mandatory Hallmarking Order page |
| hm_order_2020 | 2 | Hallmarking of Gold Jewellery and Gold Artefacts Order, 2020 |
| hm_regs_amdt_2026 | 2 | Hallmarking Amendment Regulations, 2026 |
| qco_222196 | 2 | Bureau of Indian Standards Rules, 1987 (222196) |
| qco_244425 | 2 | Order further to amend the Polyurethanes (Quality Control) Order, 2021 |
| qco_246575 | 2 | Order further to amend the Automobile Wheel Rim Component (Quality Con |
| qco_acetic_acid_methanol_aniline_qco | 2 | Acetic acid Methanol Aniline QCO |
| qco_acetic_acid_qco_2019_withdraw_order_23072025 | 2 | Acetic Acid QCO 2019 Withdraw Order 23072025 |
| qco_acrylonitrile_butadiene_styrene_abs_amendment_qco_2024 | 2 | Acrylonitrile Butadiene Styrene ABS Amendment QCO 2024 |
| qco_agro_textiles_qco_2023 | 2 | Agro Textiles QCO 2023 |
| qco_air_conditioner_and_its_related_parts_hermetic_compressor_and_temperature_sensing_controls_quality_control_amendment_order_2025 | 2 | Air Conditioner and its related Parts Hermetic Compressor and Temperat |
| qco_air_conditioner_and_its_related_parts_hermetic_compressor_and_temperature_sensing_controls_quality_control_amendment_order_2025_1_1 | 2 | Air Conditioner and its related Parts Hermetic Compressor and Temperat |
| qco_air_conditioner_and_its_related_parts_hermetic_compressor_and_temperature_sensing_controls_quality_control_amendment_order_2026_2 | 2 | Air Conditioner and its related Parts Hermetic Compressor and Temperat |
| qco_air_conditioner_qco | 2 | This Order may be called the Air Conditioner and its related Parts, He |
| qco_air_conditioner_qco_amendment_order_2025 | 2 | Air Conditioner QCO Amendment Order 2025 |
| qco_air_conditioner_qco_extension_order | 2 | Air conditioner QCO extension order |
| qco_air_cooler_and_air_filters_quality_control_2023 | 2 | Air Cooler and Air Filters Quality Control 2023 |
| qco_amendment_in_the_morpholine_quality_control_order_2020 | 2 | Amendment in the Morpholine Quality Control Order 2020 |
| qco_amendment_order_25_february_2022_compressed_compressed_1 | 2 | Amendment order 25 February 2022 compressed compressed 1 |
| qco_aniline_qco_2019_withdraw_order_23072025_1 | 2 | Bureau of Indian Standards, hereby withdraws the Acetic Acid (Quality  |
| qco_automobile_wheel_rim_component | 2 | Automobile Wheel Rim Component |
| qco_automobile_wheel_rim_component_quality_control_amendment_order_2021 | 2 | Automobile Wheel Rim Component Quality Control Amendment Order 2021 |
| qco_automobile_wheel_rim_component_quality_control_order_2020 | 2 | Automobile Wheel Rim Component Quality Control Order 2020 |
| qco_beta_picoline_qco_2020_rescind_order | 2 | Beta Picoline QCO 2020 Rescind Order |
| qco_beta_picoline_sodium_tripolyphosphate_and_pyridine_qco | 2 | Beta Picoline Sodium Tripolyphosphate and Pyridine QCO |
| qco_beta_picoline_sodium_tripolyphosphate_pyridine_qco_amendment_orders | 2 | Beta Picoline Sodium Tripolyphosphate Pyridine QCO Amendment Orders |
| qco_bicycle | 2 | Bicycles- Retro Reflective Devices (Quality Control) Order, 2021 (Bicy |
| qco_bicycles_retro_reflective_devices_quality_control_amendment_order_2024 | 2 | Bicycles Retro Reflective Devices Quality Control Amendment Order 2024 |
| qco_cookware_utensils_and_cans_for_foods_and_beverages_qco_2024 | 2 | Cookware Utensils and cans for foods and beverages QCO 2024 |
| qco_copper_product_quality_control_amendment_order_2025 | 2 | Copper Product Quality Control Amendment Order 2025 |
| qco_copper_product_quality_control_amendment_order_2026 | 2 | Copper product quality control amendment order 2026 |
| qco_cotton_bales_qco_2023 | 2 | Bureau of Indian Standards, hereby makes the following order to amend  |
| qco_cotton_bales_qco_amndment_2023_28082023 | 2 | Bureau of Indian Standards, hereby makes the following order to amend  |
| qco_cotton_bales_qco_extension1 | 2 | Bureau of Indian Standards, hereby makes the following order to amend  |
| qco_cotton_bales_quality_control_amendment_order_2023 | 2 | Cotton Bales Quality Control Amendment Order 2023 |
| qco_cross_recessed_screws_quality_control_amendment_order_2026 | 2 | Cross Recessed Screws Quality Control Amendment Order 2026 |
| qco_de_notification_foodproducts | 2 | De notification FoodProducts |
| qco_e_gazette_notification | 2 | Refrigerating Appliances (Quality Control) Order, 2020 (e Gazette noti |
| qco_electrical_accessories1 | 2 | This order may be called the Electrical Accessories (Quality Control)  |
| qco_electrical_accessories_quality_control_amendment_order_2026 | 2 | Electrical Accessories Quality Control Amendment order 2026 |
| qco_electronics_and_information_technology_goods_2021_amendment_standalone_hard_disk_drives_1 | 2 | Amendments to the Electronics and Information Technology Goods (Requir |
| qco_ethylene_dichloride_quality_control_amendment_order_2025 | 2 | Ethylene Dichloride Quality Control Amendment Order 2025 |
| qco_ethylene_vinyl_acetate_copolymers_quality_control_amendment_order_2025 | 2 | Ethylene Vinyl Acetate Copolymers Quality Control Amendment Order 2025 |
| qco_eva_qco_2024 | 2 | Order further to amend the Ethylene Vinyl Acetate Copolymers (Quality  |
| qco_extension_notification_ac_qco | 2 | Extension notification AC QCO |
| qco_extension_notification_plug_and_socket | 2 | Extension Notification Plug and Socket |
| qco_extension_of_enforcement_date_of_3_qcos | 2 | Extension of enforcement date of 3 QCOs |
| qco_extension_of_enforcement_date_of_qco_of_morpholine_acetic_acid_methanol_aniline | 2 | Extension of enforcement date of QCO of Morpholine Acetic Acid Methano |
| qco_extension_of_ethylene_glycol_qco23032023 | 2 | Extension of Ethylene Glycol QCO23032023 |
| qco_extension_of_safety_glass_qco | 2 | Order further to amend the Safety Glass (Quality Control)Order, 2020 ( |
| qco_extension_of_time_line_for_compliance_dated_01_01_2021 | 2 | Extension of time line for compliance dated 01.01.2021 |
| qco_extension_order_float_glass | 2 | Order to amend the Transparent Float Glass (Quality Control) Order, 20 |
| qco_extension_order_pressure_cooker | 2 | (Quality Control) Order, 2020 (S.O. 294 (E) dated 21/01/2020) Domestic |
| qco_extension_order_safety_glass | 2 | Order to amend the Safety Glass (Quality Control) Order, 2020 (Extensi |
| qco_flame_producing_lighters_qco_2023_1 | 2 | This Order may be called the Flame- Producing Lighters (Quality Contro |
| qco_flame_producing_lighters_quality_control_amendment_order_2024 | 2 | Flame Producing Lighters Quality Control Amendment Order 2024 |
| qco_footwear_made_from_all_rubber_and_all_polymeric_material_amend_qco_2022 | 2 | Footwear made from all rubber and all Polymeric material Amend. QCO 20 |
| qco_footwear_made_from_all_rubber_and_all_polymeric_material_and_its_components_quality_control_amendment_order_2021 | 2 | Footwear made from all Rubber and all Polymeric material and its compo |
| qco_footwear_made_from_all_rubber_and_all_polymeric_material_and_its_components_quality_control_amendment_order_2026 | 2 | Footwear made from All Rubber and all Polymeric Material and its Compo |
| qco_footwear_made_from_all_rubber_and_all_polymeric_material_and_its_qco | 2 | Footwear made from All Rubber and all Polymeric Material and its QCO |
| qco_footwear_made_from_leather_and_other_material_quality_control_amendment_order_2026 | 2 | Footwear made from Leather and other Material Quality Control Amendmen |
| qco_footwear_made_from_leather_and_other_materials_amend_qco_2022 | 2 | Footwear Made from Leather and other Materials amend. QCO 2022 |
| qco_footwear_made_from_leather_and_other_materials_qco | 2 | Footwear made from Leather and other Materials QCO |
| qco_footwear_made_from_leather_and_other_materials_quality_control_amendment_order_2021 | 2 | Footwear made from Leather and other materials Quality Control Amendme |
| qco_furniture_quality_control_amendment_order_2026 | 2 | Furniture Quality Control Amendment Order 2026 |
| qco_furniture_quality_control_second_amendment_order_2026 | 2 | Furniture Quality Control Second Amendment Order 2026 |
| qco_gazette_notification | 2 | This Order may be called the Footwear Made from all Rubber and all Pol |
| qco_geo_textiles_qco_1 | 2 | This Order may be called the Geo Textiles (Quality Control) Order, 202 |
| qco_gypsum_based_building_materials_amendment_qco_2024 | 2 | Gypsum based Building Materials Amendment QCO 2024 |
| qco_h_acid_qco_2024_rescind_order | 2 | India in the Ministry of Chemicals and Fertilizers, Department of Chem |
| qco_h_acid_quality_control_amendment_2025 | 2 | H Acid Quality Control Amendment 2025 |
| qco_h_acid_quality_control_second_amendment_order_2025 | 2 | H Acid Quality Control Second Amendment Order 2025 |
| qco_hand_tools_qco_2024 | 2 | This order may be called the Hand Tools (Quality Control) Order, 2024  |
| qco_insulated_flask_botles_and_containers_for_domestic_use_qco_2023 | 2 | Insulated Flask Botles and Containers for Domestic Use QCO 2023 |
| qco_insulated_flask_bottles_and_containers_for_domestic_use_qco_29 | 2 | Insulated Flask Bottles and Containers for Domestic Use QCO 29 |
| qco_k_acid_qco_2024_rescind_order | 2 | India in the Ministry of Chemicals and Fertilizers, Department of Chem |
| qco_k_acid_quality_control_amendment_2025 | 2 | K Acid Quality Control Amendment 2025 |
| qco_laboratory_glassware_quality_control_amendment_order_2024 | 2 | Laboratory Glassware Quality Control Amendment Order 2024 |
| qco_medical_textiles_qco_2023 | 2 | This Order may be called the Medical Textiles (Quality Control) Order, |
| qco_medical_textiles_qco_2024 | 2 | Medical Textiles (Quality Control) Order, 2023 (Medical Textiles QCO 2 |
| qco_medical_textiles_quality_control_amendment_order_2025 | 2 | Medical Textiles Quality Control Amendment Order 2025 |
| qco_medical_textiles_quality_control_second_amendment_order_2025 | 2 | MEDICAL TEXTILES QUALITY CONTROL SECOND AMENDMENT ORDER 2025 |
| qco_methanol_qco_2019_withdraw_order_23072025 | 2 | Bureau of Indian Standards, hereby withdraws the Acetic Acid (Quality  |
| qco_miety_qco_amendment_order_26_april_2023 | 2 | Miety QCO amendment order 26 April 2023 |
| qco_migration_to_is_iec_62368_part_1_2023_from_is_13252_part_1_2010_and_is_616_2017 | 2 | Migration to IS IEC 62368 Part 1 2023 from IS 13252 Part 1 2010 and IS |
| qco_notifications_for_extension_of_qco_of_aniline_morpholine_acetic_acid_and_methanol_compressed | 2 | Notifications for extension of QCO of Aniline Morpholine Acetic Acid a |
| qco_ortho_phosphoric_acid_quality_controlamendment_order_2024 | 2 | Ortho Phosphoric Acid Quality ControlAmendment order 2024 |
| qco_personal_protective_equipment_footwear_quality_control_amendment_order_2021 | 2 | Personal Protective Equipment Footwear Quality Control Amendment Order |
| qco_phthalic_anhydride_quality_control_amendment_order | 2 | Phthalic Anhydride Quality Control Amendment Order |
| qco_poly_vinyl_chloride_pvc_homopolymers_qco_2024 | 2 | Poly Vinyl Chloride PVC Homopolymers QCO 2024 |
| qco_poly_vinyl_chloride_pvc_homopolymers_quality_control_amendment_order_2024 | 2 | Poly Vinyl Chloride PVC Homopolymers Quality Control Amendment Order 2 |
| qco_poly_vinyl_chloride_pvc_homopolymers_quality_control_amendment_order_2025 | 2 | Poly Vinyl Chloride PVC Homopolymers Quality Control Amendment Order 2 |
| qco_polycarbonate_qco_2024 | 2 | Order further to amend the Polycarbonate (Quality Control) Order, 2021 |
| qco_polycarbonate_quality_control_amendment_order_2025 | 2 | Polycarbonate Quality Control Amendment Order 2025 |
| qco_polyester_continuous_filament_fully_drawn_yarn_qc_amendment_order_2024 | 2 | Polyester Continuous Filament Fully Drawn yarn QC Amendment Order 2024 |
| qco_polyethylene_material_for_moulding_and_extrusion_quality_control_amendment_order_2025_pdf | 2 | Polyethylene Material for Moulding and Extrusion Quality Control Amend |
| qco_polypropylene_pp_materials_for_moulding_and_extrusion_qco_2024 | 2 | Polypropylene PP Materials for Moulding and Extrusion QCO 2024 |
| qco_polypropylene_pp_materials_for_moulding_and_extrusion_quality_control_amendment_order_2024 | 2 | Polypropylene PP Materials for moulding and extrusion Quality Control  |
| qco_polypropylene_pp_materials_for_moulding_and_extrusion_quality_control_amendment_order_2025 | 2 | Polypropylene PP Materials for Moulding and Extrusion Quality Control  |
| qco_polypropylene_pp_materials_for_moulding_and_extrusion_quality_control_second_amendment_order_2025 | 2 | Polypropylene PP Materials for Moulding and Extrusion Quality Control  |
| qco_potable_water_bottles_qco | 2 | Order to amend the Potable Water Bottles (Quality Control) Order, 2024 |
| qco_pottable_wtaer_bottles_qco_2023_1 | 2 | This Order may be called the Potable Water Bottles (Quality Control) O |
| qco_protective_textiles_qco_1 | 2 | This Order may be called the Protective Textiles (Quality Control) Ord |
| qco_protextive_textiles_qc_upholstered_composites_used_fror_non_domestic_furniture_order_2024 | 2 | Protextive Textiles QC upholstered Composites used fror non domestic F |
| qco_pyridine_qco_2020_rescind_order | 2 | India in the Ministry of Chemicals and Fertilizers, Department of Chem |
| qco_qco_amendment_by_dcpc | 2 | Maleic Anhydride (Quality Control) Order 2022 (QCO amendment by DCPC) |
| qco_qco_extension_for_03_petrochemicals | 2 | QCO Extension for 03 Petrochemicals |
| qco_refrigerating_appliances_qco_2025 | 2 | Refrigerating Appliances QCO 2025 |
| qco_rescind_ethylene_dichloride_qco_2021 | 2 | Rescind Ethylene Dichloride QCO 2021 |
| qco_rescind_flux_cored_solder_wire_quality_control_order | 2 | Rescind Flux Cored Solder Wire Quality Control Order |
| qco_rescind_methyl_acrylate_ethyl_acrylate_qco_2021 | 2 | Rescind Methyl Acrylate Ethyl Acrylate QCO 2021 |
| qco_rescind_order_of_acid_oil_quality_control_order_2022 | 2 | Rescind Order of Acid Oil Quality Control Order 2022 |
| qco_rescind_order_of_coconut_fatty_acids_quality_control_order_2022 | 2 | Rescind Order of Coconut Fatty Acids Quality Control Order 2022 |
| qco_rescind_order_of_hydrogenated_rice_bran_fatty_acids_quality_control_order_2022 | 2 | Rescind Order of Hydrogenated Rice Bran Fatty Acids Quality Control Or |
| qco_rescind_order_of_lauric_acid_quality_control_order_2022 | 2 | Rescind Order of Lauric Acid Quality Control Order 2022 |
| qco_rescind_order_of_palm_fatty_acids_quality_control_order_2022 | 2 | Rescind Order of Palm Fatty Acids Quality Control Order 2022 |
| qco_rescind_order_of_rice_bran_fatty_acids_quality_control_order_2022 | 2 | Rescind Order of Rice Bran Fatty Acids Quality Control Order 2022 |
| qco_rescind_p_xylene_qco_2021 | 2 | Xylene (Quality Control) Order, 2021 (Rescind p Xylene QCO 2021) |
| qco_rescind_toluene_qco_2021 | 2 | Xylene (Quality Control) Order, 2021 (Rescind Toluene QCO 2021) |
| qco_rescind_vinyl_acetate_monomer_qco_2021 | 2 | Rescind Vinyl Acetate Monomer QCO 2021 |
| qco_rescind_vinyl_chloride_monomer_qco_2020 | 2 | Rescind Vinyl Chloride Monomer QCO 2020 |
| qco_ropes_and_cordages_qco_2024_1 | 2 | This Order may be called the Ropes and Cordages (Quality Control) Orde |
| qco_ropes_and_cordagesquality_control_amendment_order_2026 | 2 | ropes and cordagesquality control amendment order 2026 |
| qco_safes_safe_deposit_locker_cabinets_and_key_locks_qco | 2 | Safes Safe Deposit locker cabinets and key locks QCO |
| qco_safety_glass_amendment_order | 2 | Order further to amend the Safety glass (Quality Control) Order, 2020  |
| qco_saftey_glass_extension | 2 | Order further to amend the Safety Glass (Quality Control) Order, 2020  |
| qco_so_3207e | 2 | Three Phase Squirrel Cage (Quality Control) Order, 2017 (SO 3207E) |
| qco_so_no_2758_e | 2 | SO No. 2758 (E) |
| qco_so_no_344_e | 2 | Bureau of Indian Standards Rules, 1987 (SO No 344 (E)) |
| qco_sodium_tripolyphosphate_qco_2020_rescind_order | 2 | Sodium Tripolyphosphate QCO 2020 Rescind Order |
| qco_solar_inverter_qco_extension1 | 2 | Solar Inverter QCO extension1 |
| qco_solar_systems_devices_and_components_goods_order_2025 | 2 | Solar Systems Devices and Components Goods Order 2025 |
| qco_steel_and_steel_products_quality_control_amendment_order_2025 | 2 | Steel and Steel Products Quality Control Amendment Order 2025 |
| qco_steel_and_steel_products_quality_control_amendment_order_2026_1 | 2 | Steel and Steel Products Quality Control Amendment Order 2026 1 |
| qco_steel_tubes_quality_control_order_2020 | 2 | Steel Tubes Quality Control Order 2020 |
| qco_styrene_butadiene_rubber_latex_quality_control_amendment_order_2024 | 2 | Styrene Butadiene Rubber Latex Quality Control Amendment Order 2024 |
| qco_the_bolts_nuts_fastners_qco_2023_1 | 2 | This Order may be called The Bolts, Nuts and Fasteners (Quality Contro |
| qco_tin_ingot_quality_control_amendment_order_2025 | 2 | Tin Ingot Quality Control Amendment Order 2025 |
| qco_toluene | 2 | Toluene (Quality Control) Order, 2021 (Toluene) |
| qco_toluene_qco_2024 | 2 | Bureau of Indian Standards, hereby makes the following Order further t |
| qco_toys_extension | 2 | Order to amend the Toys (Quality Control) Order, 2020 (Toys Extension) |
| qco_toys_qco_2024 | 2 | Order further to amend the Toys (Quality Control) Order, 2020 (Toys QC |
| qco_toys_quality_control_second_amendment_order_2020 | 2 | Toys Quality Control Second Amendment Order 2020 |
| qco_v_belt_qco_2024 | 2 | Order to amend the V-Belt (Quality Control) Order, 2024 (V Belt QCO 20 |
| qco_vinyl_acetate_monomer_and_methyl_acrylate | 2 | Vinyl Acetate Monomer and Methyl Acrylate |
| qco_vinyl_chloride_monomer_quality_control_amendment_order_2025 | 2 | Vinyl Chloride Monomer Quality Control Amendment Order 2025 |
| qco_vinyl_sulphone_qco_2024_rescind_order | 2 | Vinyl Sulphone QCO 2024 Rescind Order |
| qco_vinyl_sulphone_quality_control_2025 | 2 | Vinyl Sulphone Quality Control 2025 |
| qco_vinyl_sulphone_quality_control_second_amendment_order_2025 | 2 | Vinyl Sulphone Quality Control Second Amendment Order 2025 |
| qco_whell_rim_qco_amendment_2022 | 2 | Order further to amend the Automobile Wheel Rim Component (Quality Con |
| cert_apply_online | 1 | Apply Online |
| cert_process | 1 | Product Certification Process |
| fmcs_fee | 1 | FMCS Fee |
| bis_care_app_page | 1 | BIS apps (BIS CARE) |
| consumer_complaint | 1 | Online complaint registration |
| crs_amdt_mar_2026 | 1 | CRS Order amendment S.O.1246(E), 10 Mar 2026 |
| ca_amdt_2026_corrigendum | 1 | Corrigendum to CA Amendment, 2026 |
| qco_100_percent_polyester_spun_grey_and_white_yarn_quality_control_order_2021 | 1 | 100 Percent Polyester Spun Grey and White Yarn Quality Control Order 2 |
| qco_acetic_acid_amendment_order | 1 | Central Government hereby makes the following amendment in the Acetic  |
| qco_acetic_acid_qco_extension | 1 | Central Government hereby makes the following amendment in the Acetic  |
| qco_acetone_extension | 1 | Central Government hereby makes the following amendment in the Acetone |
| qco_acetone_extension_2 | 1 | Central Government hereby makes the following amendment in the Acetone |
| qco_acitic_acid_amendment_order | 1 | Central Government hereby makes the following amendment in the Acetic  |
| qco_agro_textiles | 1 | This Order may be called the Agro Textiles (Quality Control) Amendment |
| qco_al_and_al_alloys_qcoamendment2024 | 1 | Bureau of Indian Standards, hereby makes the following Order to amend  |
| qco_aluminium_aluminium_alloy_qco_2023 | 1 | Aluminium Aluminium Alloy QCO 2023 |
| qco_aluminium_amended_qco_2023 | 1 | Bureau of Indian Standards, hereby makes the following Order to amend  |
| qco_aluminium_and_aluminium_alloys_quality_control_order_2023_withdrawal_order | 1 | Aluminium and Aluminium Alloys Quality Control Order 2023 Withdrawal O |
| qco_aluminum_and_aluminium_products_qc_amend_order_2024 | 1 | Aluminum and Aluminium Products QC Amend Order 2024 |
| qco_amendment_in_the_acetone_quality_control_order_2020 | 1 | Amendment in the Acetone Quality Control Order 2020 |
| qco_amendment_in_the_beta_picoline_quality_control_order_2020 | 1 | Amendment in the Beta Picoline Quality Control Order 2020 |
| qco_amendment_in_the_gamma_picoline_quality_control_order_2020 | 1 | Amendment in the Gamma Picoline Quality Control Order 2020 |
| qco_amendment_in_the_hydrogen_peroxide_quality_control_order_2020 | 1 | Amendment in the Hydrogen Peroxide Quality Control Order 2020 |
| qco_amendment_in_the_potassium_carbonate_quality_control_order_2020 | 1 | Amendment in the Potassium Carbonate Quality Control Order 2020 |
| qco_amendment_in_the_pyridine_quality_control_order_2020 | 1 | Amendment in the Pyridine Quality Control Order 2020 |
| qco_amendment_in_the_sodium_tripolyphosphate_quality_control_order_2020 | 1 | Amendment in the Sodium Tripolyphosphate Quality Control Order 2020 |
| qco_amendment_order_18112022 | 1 | Central Government hereby makes the following amendment in the Methyle |
| qco_amendment_to_the_electronics_and_information_technology_goods_requirement_of_compulsory_registration_order_2021 | 1 | Amendment to the “Electronics and Information Technology Goods (Requir |
| qco_amendments_to_the_electronics_and_information_technology_goods_requirements_for_compulsory_registration_2021_1 | 1 | amendments to the Electronics and Information Technology Goods Require |
| qco_aniline_amendment_order_3f9e99 | 1 | This Order may be called the Aniline (Quality Control) Order, 2019 (An |
| qco_aniline_qco_extension | 1 | Central Government hereby makes the following amendment in the Aniline |
| qco_beta_picoline_amendment_order | 1 | Beta Picoline Amendment Order |
| qco_copper_qcoamendment_2024 | 1 | Bureau of Indian Standards, hereby makes the following Order to amend  |
| qco_copper_quality_control_amendment_order_2023 | 1 | Copper Quality Control Amendment Order 2023 |
| qco_copper_quality_control_order_2023_withdrawal_order | 1 | Copper Quality Control Order 2023 Withdrawal Order |
| qco_corrigendum_80bd3b | 1 | Corrigendum |
| qco_corrigendum_87cee8 | 1 | corrigendum |
| qco_corrigendum_for_quality_control_order_for_ethylene_glycol2020_0 | 1 | Corrigendum for Quality Control Order for Ethylene Glycol2020 0 |
| qco_corrigendum_of_gypsum_based_building_materials_quality_control_order_2024 | 1 | Corrigendum of Gypsum based Building Materials Quality Control Order 2 |
| qco_corrigndum_for_bicycyle_reflector_27032023 | 1 | Corrigndum for Bicycyle reflector 27032023 |
| qco_cotton_bales_qco_20231 | 1 | This Order may be called the Cotton Bales (Quality Control) Order, 202 |
| qco_digital_television_receiver_for_satellite_broadcast_transmission_qco_amendment_2025 | 1 | Digital Television Receiver for Satellite Broadcast Transmission QCO A |
| qco_extension_acetic_aciddcpc | 1 | Central Government hereby makes the following amendment in the Acetic  |
| qco_extension_aniline_dcpc | 1 | Central Government hereby makes the following amendment in the Aniline |
| qco_extension_in_the_date_of_enforcement_of_quality_control_order_on_is_3748_is_7291_and_is_12146 | 1 | Extension in the date of enforcement of Quality Control Order on IS 37 |
| qco_extension_in_timelines_for_the_implementation_of_television_sets_is_18112 | 1 | Extension in timelines for the implementation of Television Sets IS 18 |
| qco_extension_in_timelines_for_the_implementation_of_the_order_for_product_categories_included_in_the_schedule_of_cro_vide_s_o_1929e_published_in_gazette_of_india_on_26th_april20 | 1 | Extension in timelines for the implementation of the order for product |
| qco_extension_methanol_dcpc | 1 | Central Government hereby makes the following amendment in the Methano |
| qco_extension_of_date_of_implementation_of_ac_qcopdf_1 | 1 | Extension of Date of implementation of AC QCOpdf 1 |
| qco_extension_of_methylene_chloride_and_ortho_phosphoric_acid | 1 | Extension of Methylene Chloride and Ortho Phosphoric Acid |
| qco_extension_of_televisoin_sets_timelies | 1 | Extension of Televisoin Sets timelies |
| qco_extension_order_sheet_glass | 1 | Order to amend the Flat Transparent Sheet Glass (Quality Control) Orde |
| qco_footwear_made_from_all_rubber_and_all_polymeric_material_and_its_components_quality_control_amendment_order_2020 | 1 | Footwear made from all Rubber and all Polymeric material and its compo |
| qco_footwear_made_from_leather_and_other_materials_quality_control_amendment_order_2020 | 1 | Footwear made from Leather and other materials Quality Control Amendme |
| qco_gamma_picolin_amendment_order | 1 | Gamma Picolin Amendment Order |
| qco_gazette_notification_of_hydrogen_peroxide_dated_24_08_2022 | 1 | Gazette Notification of Hydrogen Peroxide dated 24.08.2022 |
| qco_geo_textiles_quality_controlamendment_order_2023 | 1 | Geo Textiles Quality ControlAmendment Order 2023 |
| qco_geotextiles_qco_2024_1 | 1 | This Order may be called the Geotextiles (Quality Control) Order, 2024 |
| qco_gsr_no_759_e | 1 | GSR NO 759(E) |
| qco_gsr_no_759_e_b64cf9 | 1 | GSR NO 759(E) |
| qco_gsr_no_759_e_dc3eaf | 1 | GSR NO 759(E) |
| qco_gsr_no_760_e | 1 | GSR No 760(E) |
| qco_helmet_for_riders_of_two_wheeler_motor_vehicles_quality_control_order_2020 | 1 | Helmet for riders of Two Wheeler Motor Vehicles Quality Control Order  |
| qco_hydrogen_peroxide_amendment_order | 1 | Hydrogen Peroxide Amendment Order |
| qco_indutech_qco_2024 | 1 | This Order may be called the Indutech (Quality Control) Order, 2024 (I |
| qco_laboratory_glassware | 1 | This order may be called the Laboratory Glassware (Quality Control) Or |
| qco_linear_alkyl_benzene_quality_control_order_1 | 1 | Linear Alkyl Benzene Quality Control Order 1 |
| qco_maleic_anhydride_qco_amendment_01052023 | 1 | Maleic Anhydride QCO amendment 01052023 |
| qco_medical_textiles_quality_control_amendment_order_2024 | 1 | Medical Textiles Quality Control Amendment Order 2024 |
| qco_methanol_amendment_order_44cd3b | 1 | Methanol amendment order |
| qco_methanol_amendment_order_903bf0 | 1 | Central Government hereby makes the following amendment in the Methano |
| qco_methanol_qco_extension | 1 | Central Government hereby makes the following amendment in the Methano |
| qco_ministry_of_textiles_order_2023 | 1 | ORDER In pursuance to the Gazette Notification of the Geo Textiles (Qu |
| qco_morpholine_qco | 1 | Central Government hereby makes the following amendment in the Morphol |
| qco_morpholine_qco_2024 | 1 | Central Government hereby makes the following amendment in the Morphol |
| qco_morpholine_quality_control_order_2020 | 1 | Morpholine Quality Control Order 2020 |
| qco_n_butyl_acrylate_quality_control_order_2021 | 1 | n Butyl Acrylate Quality Control Order 2021 |
| qco_nickel_qco_amendment2024 | 1 | Bureau of Indian Standards, hereby makes the following Order to amend  |
| qco_nickel_quality_control_order_2023_withdrawal_order | 1 | Nickel Quality Control Order 2023 Withdrawal Order |
| qco_nickle_qco_2023 | 1 | This Order may be called the Nickel (Quality Control) Order, 2023 (Nic |
| qco_nickle_qco_amnd_order_2023 | 1 | Bureau of Indian Standards, hereby makes the following Order to amend  |
| qco_order_of_extension_in_date_of_enforcement_of_is_4432_is_5518_is_12145_is_13387_is_4072_is_13352_covered_under_qulaity_control_order | 1 | Order of Extension in date of enforcement of IS 4432 IS 5518 IS 12145  |
| qco_order_of_extension_in_date_of_enforcement_of_is_6529_covered_under_qulaity_control_order | 1 | Order of Extension in date of enforcement of IS 6529 covered under Qul |
| qco_order_of_extension_in_date_of_enforcement_of_is_7226_and_is_14331_covered_under_qulaity_control_order | 1 | Order of Extension in date of enforcement of IS 7226 and IS 14331 cove |
| qco_ortho_phosphoric_acid_quality_control_second_amendment_order_2024 | 1 | Ortho Phosphoric Acid Quality Control Second Amendment order 2024 |
| qco_personal_protective_equipment_footwear_quality_control_amendment_order_2020 | 1 | Personal Protective Equipment Footwear Quality Control Amendment Order |
| qco_polyester_staple_fibre_qco_amendement_2023 | 1 | Polyester Staple Fibre QCO Amendement 2023 |
| qco_polyethylene_material_for_moulding_and_extrusion | 1 | Polyethylene Material for Moulding and Extrusion |
| qco_potassium_carbonate_amendment_order | 1 | Potassium Carbonate Amendment Order |
| qco_primary_lead_quality_control_amendment_order_2025 | 1 | Primary Lead Quality Control Amendment Order 2025 |
| qco_primary_lead_quality_control_order_2025 | 1 | Primary Lead Quality Control Order 2025 |
| qco_primary_lead_quality_control_order_2025_withdrawal_order | 1 | Primary Lead Quality Control Order 2025 Withdrawal Order |
| qco_protective_textiles_qco_amendment_2024 | 1 | Protective Textiles QCO amendment 2024 |
| qco_protective_textiles_quality_controlamendment_order_2023 | 1 | Protective Textiles Quality ControlAmendment Order 2023 |
| qco_pyridin_amendment_order | 1 | Central Government hereby makes the following amendment in the Pyridin |
| qco_qco_amendement_order_for_p_xylene_polyurethanes_1 | 1 | QCO Amendement order for p Xylene Polyurethanes 1 |
| qco_refined_nickel_quality_control_amendment_order_2025 | 1 | Refined Nickel Quality Control Amendment Order 2025 |
| qco_refined_nickel_quality_control_order_2025_withdrawal_order | 1 | Refined Nickel Quality Control Order 2025 Withdrawal Order |
| qco_refined_zinc_quality_control_amendment_order_2025 | 1 | Refined Zinc Quality Control Amendment Order 2025 |
| qco_refined_zinc_quality_control_order_2025 | 1 | Refined Zinc Quality Control Order 2025 |
| qco_refined_zinc_quality_control_order_2025_withdrawal_order | 1 | Refined Zinc Quality Control Order 2025 Withdrawal Order |
| qco_rescind_order_for_footwear_made_from_all_rubber_all_polymeric_material_and_its_component_qco_2020 | 1 | Rescind order for Footwear made from all Rubber all Polymeric material |
| qco_rescind_order_for_footwear_made_from_leather_other_material_qco_2020 | 1 | Rescind order for Footwear made from Leather other material QCO 2020 |
| qco_rescind_order_of_acrylonitrile_quality_control_order_2022 | 1 | Rescind Order of Acrylonitrile Quality Control Order 2022 |
| qco_rescind_order_of_maleic_anhydride_quality_control_order_2022 | 1 | Rescind Order of Maleic Anhydride Quality Control Order 2022 |
| qco_rescind_order_of_styrene_vinyl_benzene_quality_control_order_2022 | 1 | Rescind Order of Styrene Vinyl Benzene Quality Control Order 2022 |
| qco_rescind_order_of_the_cotton_bales_quality_control_order_2023_1 | 1 | Rescind Order of the Cotton Bales Quality Control Order 2023 1 |
| qco_resin_treated_compressed_wood_laminates_qco_2023 | 1 | Resin treated compressed wood laminates QCO 2023 |
| qco_safety_glass_qco_amendment | 1 | Order further to amend the Safety Glass (Quality Control) Order, 2020  |
| qco_so_443_vsf_qco_extension_order27012023 | 1 | Viscose Staple Fibres (Quality Control) Order, 2022 (SO 443 VSF QCO Ex |
| qco_sodium_tripolyphosphate_amendment_order | 1 | Sodium Tripolyphosphate Amendment Order |
| qco_temporary_suspension_of_linear_alkyl_benzene_quality_control_order | 1 | Temporary suspension of Linear Alkyl Benzene Quality Control Order |
| qco_temporary_suspension_of_nbutyl_acrylate_quality_control_order | 1 | Temporary suspension of nButyl Acrylate Quality Control Order |
| qco_terephthalic_acid_qco | 1 | This order may be called the Terephthalic Acid (Quality Control) Order |
| qco_tin_ingot_quality_control_order_2025 | 1 | Tin Ingot Quality Control Order 2025 |
| qco_tin_ingot_quality_control_order_2025_withdrawal_order | 1 | Tin Ingot Quality Control Order 2025 Withdrawal Order |
| qco_viscose_staple_fibres_qco_2022 | 1 | This order may be called the Viscose Staple Fibres (Quality Control) O |
| qco_viscose_staple_fibres_rescind_order_2025 | 1 | Viscose Staple Fibres Rescind Order 2025 |
| qco_wood_based_board_qco_2023 | 1 | This Order may be called the Wood Based Boards (Quality Control) Order |

## 3 sample chunks per main document (first, middle, last)

### ca_regulations_2018 (220 chunks): BIS (Conformity Assessment) Regulations, 2018
- `ca_regulations_2018::0000` · p.2 · (no section)  
  > ₹ 37,000.00 ₹ 17.30 ₹ 0.00 ₹ 0.00 11:2006 ₹ 46,000.00 ₹ 37,000.00 ₹ 1.75 ₹ 0.00 ₹ 0.00 ₹ 73,000.00 ₹ 60,000.00 ₹ 0.27 ₹ 0.00 ₹ 0.00 ₹ 58,000.00 ₹ 47,000.00 ₹ 0.90 ₹ 0.00 ₹ 0.00 ₹ 58,000.00 ₹ 47,000.00 ₹ 0.27 ₹ 0.00 ₹ 0.00 ₹ 58,000.00 ₹ 47,000.00 ₹ 0.42 ₹ 0.00 ₹ 0.00 2.5 1.9 0.2 0.4 - 3.8 0.4 0.8 0.1
- `ca_regulations_2018::0110` · p.287 · Form - IX > Scheme-I  
  > the Indian Standard Mark is marked, to the relevant Indian Standard. 10.4 The manufacturer further undertakes to furnish a Bank Guarantee, as per the prescribed format, for USD 10000 (US Dollars Ten Thousand only) in favour of BIS, for due compliance of the provisions of the BIS Act, 2016 and the ru
- `ca_regulations_2018::0219` · p.412 · Form - IV > Scheme-VII > Substituted vide Gazette notification No. F. No. BS/11/11/2018 dated 12 October 2018  
  > # Substituted vide Gazette notification No. F. No. BS/11/11/2018 dated 12 October 2018

### bis_act_2016 (149 chunks): Bureau of Indian Standards Act, 2016
- `bis_act_2016::0000` · p.1 · (no section)  
  > jftLVªh lañ Mhñ ,yñ—(,u)04@0007@2003—16 vlk/kkj.k Hkkx II — [k.M 1 izkf/kdkj ls izdkf'kr PUBLISHED BY AUTHORITY lañ 12] ubZ fnYyh] eaxyokj] ekpZ 22] 2016@pS= 2] 1938 ¼'kd½ No. 12] NEW DELHI, TUESDAY, MARCH 22, 2016/CHAITRA 2, 1938 (SAKA) bl Hkkx esa fHkUu i`"B la[;k nh tkrh gS ftlls fd ;g vyx ladyu 
- `bis_act_2016::0074` · p.8 · CHAPTER III > Section 14(6) Certification of Standard Mark of jewellers and sellers of certain specified goods or articles  
  > (6) No testing and marking centre or assaying and hallmarking centre, other than the recognised by the Bureau, shall with respect to goods or articles notified under sub-section (1), use, affix, emboss, engrave, print or apply in any manner the Standard Mark, including the Hallmark, or colourable im
- `bis_act_2016::0148` · p.17 · CHAPTER V > Section 43(3)  
  > (3) The mention of particular matters in sub-section (2) shall not be held to prejudice or affect the general application of section 6 of the General Clauses Act, 1897 with regard to the effect of repeal. [10 of 1897.] DR. REETA VASISHTA, Additional Secretary to the Govt. of India. PRINTED BY THE GE

### upcoming_qcos (121 chunks): Upcoming QCOs notified and due for implementation
- `upcoming_qcos::0000` · p.- · (no section)  
  > [Home](https://www.bis.gov.in/?lang=en "Home") [Standard of the Week](https://www.bis.gov.in/index.php/standard-of-the-week/?lang=en "Standard of the Week") [Standard of the Month](https://www.bis.gov.in/index.php/standard-of-the-month/?lang=en "Standard of the Month") [New Standards](https://www.se
- `upcoming_qcos::row0058` · p.- · 01 October, 2026: Commercial Electric Doughnut Fryers and Deep Fat Fryers  
  > Product: Commercial Electric Doughnut Fryers and Deep Fat Fryers / 01 October, 2026 / Upcoming QCO (notified, due for implementation) / Enforcement Date: 01 October, 2026 / Ministry Department: Department for Promotion of Industry and Internal Trade / Product 2: IS 302 (Part 1) : 2024 IEC 60335-1:20
- `upcoming_qcos::row0118` · p.- · IS 5175:2022: Fibre Ropes — Polypropylene Split Film, Monofilament And Multifilament ( PP2 ) and Polypropylene High-Tena  
  > Product: Fibre Ropes — Polypropylene Split Film, Monofilament And Multifilament ( PP2 ) and Polypropylene High-Tenacity Multifilament ( PP3 ) —3-, 4-, 8- and 12- Strand Ropes / IS 5175:2022 / Upcoming QCO (notified, due for implementation) / Enforcement Date: 05 June 2027 / Ministry Department: Mini

### scheme2_page (76 chunks): Scheme II (CRS registration) page
- `scheme2_page::0000` · p.- · Scheme - II (Registration Scheme)  
  > ## Scheme - II (Registration Scheme) **1. List of Electronics and IT Goods under ‘Compulsory Registration Scheme’ for Self Declaration of conformity-Notified by Ministry Of Electronics And Information Technology** **2. List of Solar Photovoltaics, Systems, Devices and Components under Compulsory Reg
- `scheme2_page::row0037` · p.- · IS 16242 (Part 1):2014: UPS/Inverters of rating ≤ 10kVA  
  > Product: UPS/Inverters of rating ≤ 10kVA / IS 16242 (Part 1):2014 / Scheme II (CRS registration) / QCO: SO 2742 (E), dated 17th August 2017 Superseded by Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2021 Essential Requirement(s) for CCTV as per Annexur
- `scheme2_page::row0074` · p.- · IS 12171:2019: Cotton Bales  
  > Product: Cotton Bales / IS 12171:2019 / Scheme II (CRS registration) / QCO: Cotton Bales (Quality Control) Order, 2023 S.O. 948(E), dated 28 February 2023 Cotton Bales (Quality Control) Amendment Order, 2023 S.O. 3557(E), dated 07 August 2023 Cotton Bales (Quality Control) Amendment Order, 2023 S.O.

### guide_grant_of_licence (67 chunks): Guidelines for Grant of Licence (Scheme I, 25 Feb 2026)
- `guide_grant_of_licence::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:1 25 February 2026 Sub: Guidelines for Grant of Licence (GoL) as per the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 This document stipulates the guidelines for Grant 
- `guide_grant_of_licence::0033` · p.19 · Annexure-II (C) > Scheme-I  
  > Irrigation Equipment - Strainer-type Filters Pulverized Fuel Ash-lime Bricks Shunt Power Capacitors Of The Self-healing Type For Ac Systems Having A Rated Voltage Up To And Including 1 000 V Part 1 General Performance, Testing And Rating [ 346 IS 13340 (Part 1) ] Safety Requirements -- Guide For Ins
- `guide_grant_of_licence::0066` · p.62 · Annexure-XII > Scheme-I  
  > Annexure-XII Feedback prompt 1) Are you satisfied with the services of BIS? [ i) Yes ] <Optional textbox> [ ii) No ] 2) Any feedback or suggestions (optional) <Optional textbox with file upload facility>

### ca_amdt_2026 (59 chunks): CA Amendment Regulations, 2026
- `ca_amdt_2026::0000` · p.1 · (no section)  
  > No. 142] NEW DELHI, WEDNESDAY, FEBRUARY 25, 2026/PHALGUNA 6, 1947 1415 GI/2026 (1) 39.3 21.6 17.7 91.0 84.3 25.2 40.4 3.36 23.5 23.5 7.52 19.6 42.4 8.57 240.49 175.48 66.26 12.00 8.24 ----------------------------------------------------------- …………………………… …………………….) …………………. ________________________
- `ca_amdt_2026::0029` · p.55 · Form - II > 5. That M/s ……………………………… (the liaison office / subsidiary firm/branch office, in India)  
  > 5. That M/s ……………………………… (the liaison office / subsidiary firm/branch office, in India) accepts and undertakes full liability in case of violation of any provision of the Act, rules and regulations framed thereunder, arising out of any act or omission on the part of the foreign applicant. 6. That I 
- `ca_amdt_2026::0058` · p.68 · Form - VII > 4. This letter is being issued with the approval of competent authority  
  > In case of non-payment of annual fee alongwith production statement before the due date for which, the provision of regulation 8 shall apply.”. [ADVT.-III/4/Exty./711/2025-26] [ALKA, Secy.] Note: The principal regulations were published in the Gazette of India Extraordinary, Part III, Section 4 vide

### hm_regulations_2018 (51 chunks): BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1)
- `hm_regulations_2018::0000` · p.21 · (no section)  
  > 80,000/- 40,000/- 15,000/- 7,500/- 15,000/- 5,000/- 5,000/- 60,000/- 1. (i) (ii) (i) (iii) 2. (i) (ii) (i) (ii) 1000/- 1000/- 1000/- 7,000/- [(i)] [(ii)] [(iii)] 6. 1. 1.1 1.2 1.3 1.4 1.5 2. 2.1 3. 3.1 3.2 4. 4.1 4.2 5.1 6.1 6.2 7.1 8.1 9.1 9.2 10.1 12.1 12.2 12.3 12.4 ..............................
- `hm_regulations_2018::0025` · p.70 · Schedule V  
  > Schedule V (refer sub-regulation(2) of regulation 14) (refer sub-regulation(1) of regulation 17) (refer clause (c) of sub-regulation(1) of regulation 15) (refer clause (b) of sub-regulation(6) of regulation 18) Fee for Grant and Renewal of Licence to Refinery or Mint S.No. Fee Amount in Rs. Applicat
- `hm_regulations_2018::0050` · p.92 · Form – XIV > Substituted vide Gazette notification No. F. No. BS/11/05/2018 dated 12 October 2018  
  > # Substituted vide Gazette notification No. F. No. BS/11/05/2018 dated 12 October 2018

### guide_grant_coc (44 chunks): Guidelines for Grant of Certificate of Conformity (Scheme IV)
- `guide_grant_coc::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:16:1 02 May 2019 Sub: Guidelines for Grant of Certificate of Conformity as per the conformity assessment Scheme – IV of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 These guidelines stipulate the procedure f
- `guide_grant_coc::0022` · p.13 · Annexure - V > 3. The fee stipulated in Paragraph 5 of Scheme  
  > 3. The fee stipulated in Paragraph 5 of Scheme - IV of BIS (Conformity Assessment) Regulations, 2018 is payable by you regardless of the fact whether you actually cover your product or not with the BIS certification. Our Receipt No.R/ ............. dated ....................... for the CoC fee for t
- `guide_grant_coc::0043` · p.28 · Annexure – XII  
  > Annexure – XII Name of the BO/RO Name of the Applicant/Certificate holder Address with email Application No./CoC No. Specified requirement(s) Product Varieties covered Date of grant of CoC and validity Review of performance during last two years Details of order appealed against Closure notice/Cance

### guide_non_conformity (42 chunks): Guidelines for Dealing with Product Non-Conformity (25 Feb 2026)
- `guide_non_conformity::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:2 (Part 1) 25 February 2026 Subject: Guidelines for dealing with non-conformity of product(s) observed during operation of licence under Scheme - I of Schedule - II of BIS (Conformity Assessment) Regulations, 2018 - reg. S
- `guide_non_conformity::0021` · p.15 · Annexure-I  
  > Annexure-I Our Ref: ....... BO/CML- Subject: Non-conformity of sample pertaining to CM/L .................... for ……………. (Product name) as per ……………………….. (Indian Standard) [ M/s ] 1) This has reference to the BIS Certification Marks Licence No. CM/L ............................. granted to you for 
- `guide_non_conformity::0041` · p.39 · Annexure-XIII  
  > Annexure-XIII Our Ref: ....... BO/CML- Subject: Expiry of BIS Certification Licence CM/L …..…… for………. (Product name) as per ........................….….. (Indian Standard) [ M/s ] 1) This has reference to the BIS Certification Marks Licence No. CM/L-……….. granted to you for use of the BIS Standard 

### simplified_procedure_list (33 chunks): List of Products under Simplified Procedure
- `simplified_procedure_list::0000` · p.1 · (no section)  
  > www.bis.gov.in [Draft] Bureau of Indian Standards (B.I.S.) in its endeavour and commitment towards easing certification compliance to the Industry is introducing measures for mandatory utilisation of option - 2 (erstwhile simplified procedure) for processing product certification ( ) applications fo
- `simplified_procedure_list::0016` · p.1 · (no section)  
  > 506 IS 550 (Part 1) Safes Part 1 Specification 507 IS 5557 Industrial and Protective Rubber Knee and Ankle Boots 508 IS 5557 (Part 2) All Rubber Gum Boots And Ankle Boots Part 2 Occupational Purposes 509 IS 6006 Uncoated Stress Relieved Strand For Prestressed Concrete 510 IS 6192 Textiles- Monoaxial
- `simplified_procedure_list::0032` · p.1 · (no section)  
  > 1056 IS 1746 Shoe polish, paste (*) 1057 IS 177 Cotton Drills (*) 1058 IS 17880 Geosynthetics - Polymer Gabions for Coastal and Waterways Protection (*) 1059 IS 9360 Carbofuran granules, encapsulated (*) 1060 IS 15182 Propiconazole EC (*) 1061 IS 10212 (Part 1) General requirements for packages of e

### bis_rules_2018 (28 chunks): BIS Rules, 2018 (with all amendments)
- `bis_rules_2018::0000` · p.4 · (no section)  
  > (1) (2) ( ) (4) (5) ----------------------------------------------------------------------------------------------------------------- [ PUBLISHED IN THE GAZETTE OF INDIA, EXTRAORDINARY, GOVERNMENT OF INDIA MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION (Department of Consumer Affairs) NO
- `bis_rules_2018::0014` · p.45 · Rule 26. Standards promotion  
  > 26. Standards promotion. - The Bureau may promote adoption of Indian Standards by consumers, commerce, industry, Government and other interests, in such manner as it may consider necessary.
- `bis_rules_2018::0027` · p.57 · Inserted vide gazette Notification Nos. G.S.R. 1090(E) dated 06 November 2018 and  
  > ## Inserted vide gazette Notification Nos. G.S.R. 1090(E) dated 06 November 2018 and G.S.R. 1132(E) dated 20 November 2018 # Inserted vide gazette Notification No. G.S.R. 1090(E) dated 06 November 2018 * Inserted vide gazette Notification No G.S.R. 382(E) dated 29 May 2019 @ Inserted vide gazette No

### guide_unsatisfactory_performance (27 chunks): Guidelines for Dealing with Unsatisfactory Performance (25 Feb 2026)
- `guide_unsatisfactory_performance::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:2 (Part 2) 25 February 2026 Subject: Guidelines for dealing with unsatisfactory performance (other than matters related to non-conformity of the product) during operation of licence under Scheme-I of Schedule-II of BIS (Co
- `guide_unsatisfactory_performance::0013` · p.11 · 18.  
  > 18. (i) Before cancelling a licence, a cancellation notice of not less than twenty one [ Proceedings for cancellation ] days shall be given to the licensee (template attached Annexure-V ) (a) the BO shall ensure complete facts of the case are produced alongwith applicable material and documentary ev
- `guide_unsatisfactory_performance::0026` · p.25 · Annexure-VIII  
  > Annexure-VIII Our Ref: ....... BO/CML- Subject: Expiry of BIS Certification Licence CM/L …..…… for………. (Product name) as per ........................….….. (Indian Standard) [ M/s ] Kind Attn: (Name of the CEO/MD) Madam/Sir, 1) This has reference to the BIS Certification Marks Licence No. CM/L ......

### guide_factory_surveillance (21 chunks): Guidelines for Factory Surveillance (25 Feb 2026)
- `guide_factory_surveillance::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:6 25 February 2026 Subject: Guidelines for factory surveillance during operation of licence for the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 1. This document stipul
- `guide_factory_surveillance::0010` · p.9 · Annexure-I > 7. Verification of Details regarding Manufacturing Process  
  > revision of standard, shifting etc and uploaded revised list of machinery: In this section the CO/Agent will evaluate and report any changes required in Manufacturing Machinery on account of situations mentioned in section heading. After verification of revised list confirmation for same will be rec
- `guide_factory_surveillance::0020` · p.18 · Annexure-II  
  > Annexure-II Code of ethics for BIS certification officers and AGENT(s) for factory inspection While discharging its duties under the BIS Act 2016, BIS is committed to maintain the trust and respect of its stakeholders and the public at large through unquestionable integrity, honesty, behave professi

### guide_additional_scheme1 (16 chunks): Additional Guidelines for Scheme-I (DG Order No. 3 of 2020)
- `guide_additional_scheme1::0000` · p.1 · (no section)  
  > 1. DDG (Certification) Secretariat Our Ref: DDG (Cert)/38 04 August 2020 Subject: Additional guidelines for Grant of Licence (GoL), Renewal of Licence (RoL), Reducing testing time and Hand-holding & professional support to MSMEs
- `guide_additional_scheme1::0008` · p.6 · 4. Sample collection and testing  
  > is created in the BIS or BIS approved lab. 4.5. Head, Branch Office shall hold a VC with the lab/labs unable to submit the test report on time a day after the expiry of the prescribed timeframe, and bring all the cases of more-thanseven-days delay to the notice of DDGR, who shall take up the matter 
- `guide_additional_scheme1::0015` · p.11 · 10. Handholding and Professional Support to MSMEs  
  > details to all concerned licensees through the communication window of the Portal; and the Branch Offices having more than 5 licences of the product to organise a licensee meet to explain the changes and actions expected from licensees. 10.4.5. Workshop/Training/Seminar to be organised at regular in

### guide_cbtf_msme (15 chunks): Guidelines for utilisation of Cluster Based Test Facility (CBTF) by MSMEs
- `guide_cbtf_msme::0000` · p.1 · (no section)  
  > Approved 30 April 2021 BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:8 30 April 2021 Subject: Guidelines for utilisation of Cluster Based Test Facility (CBTF) by Micro, Small & Medium Enterprises (MSMEs) under conformity assessment Scheme – I of Schedule – II of BIS (
- `guide_cbtf_msme::0007` · p.6 · Annexure-I  
  > Annexure-I [Draft] (Part A) Undertaking by the manufacturer (applicant) for utilisation of CBTF {On firm’s letterhead by Authorized Signatory to concerned Head of the Branch office} ……… (Branch Office) [The Head] Bureau of Indian Standards Subject: [Application No. ....................... ] Request 
- `guide_cbtf_msme::0014` · p.19 · Annexure  
  > Annexure Code of Ethics (The code of ethics shall be furnished, signed and sealed by Proprietor or Director or Partner of the testing facility on testing facility’s official stationery (letter-head)). We, M/s _____________________________________________________________________ Testing facility loca

### hm_order_june_2021 (15 chunks): Hallmarking Order, June 2021
- `hm_order_june_2021::0000` · p.1 · (no section)  
  > www.bis.gov.in No. 2303] NEW DELHI, WEDNESDAY, JUNE 23, 2021/ASHADHA 2, 1943 3423 GI/2021 (1) MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION (Department of Consumer Affairs) ORDER New Delhi, the 23rd June, 2021 S.O. 2481(E).—In exercise of the power conferred by sub-section (3) of sectio
- `hm_order_june_2021::0007` · p.14 · 1. Akola  
  > 1. Akola 2. Amravati 3. Dhule 4. Latur 5. Nanded 6. Ratnagiri 7. Sindhudurg 8. Aurangabad 9. Nagpur 10. Palghar 11. Raigad 12. Ahmednagar 13. Solapur 14. Jalgaon 15. Nashik 16. Satara 17. Sangli 18. Kolhapur 19. Thane 20. Pune 21. Mumbai Suburban 22. Mumbai City National Capital Territory of Delhi
- `hm_order_june_2021::0014` · p.18 · 15. Dakshin Dinajpur  
  > 15. Dakshin Dinajpur 16. Malda 17. Murshidabad 18. Nadia 19. Paschim Medinipur “. [F. No. 6/1/2017-BIS (Part 2)] NIDHI KHARE, Addl. Secy. Note : The principal order was published in the Gazette of India, Extraordinary, Part II, Section 3, subsection (ii) vide number S.O. 205 (E), dated the 15th Janu

### guide_change_in_scope (12 chunks): Guidelines for Change in Scope of Licence
- `guide_change_in_scope::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:4 13 May 2021 Subject: Guidelines for Change in Scope of Licence (CSoL) and special situations as per the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 This document sti
- `guide_change_in_scope::0006` · p.5 · Annexure-II > 3. Your reply to our rejection notice was due by ..............................., but we have not received  
  > 3. Your reply to our rejection notice was due by ..............................., but we have not received any reply from you till date. (or) The reply received with your letter Ref: .................. dated ......................... has not been found satisfactory due to following reasons: (Referen
- `guide_change_in_scope::0011` · p.10 · Annexure - VII  
  > Annexure - VII Attachment to Licence No. CM/L- ............................. CM/L- Name of the Licensee with the [Indian Standard No.] Name of the Factory Address Product Endorsement No. ...... Dated .... Consequent upon the revision of IS ........................... as IS ..........................

### guide_market_surveillance (12 chunks): Guidelines for Market Surveillance (25 Feb 2026)
- `guide_market_surveillance::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:7 25 February 2026 Subject: Guidelines for market surveillance during operation of licence for the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 1. This document stipula
- `guide_market_surveillance::0006` · p.8 · Annexure-I > 5.  
  > 5. Name & Designation of Certification Officer (CO )- This section will capture the name and designation of the officer who is processing the received sample. The portal will auto fill these details based on allocation of the sample to concerned officer.
- `guide_market_surveillance::0011` · p.13 · Annexure-III  
  > Annexure-III Code of ethics for BIS certification officers and AGENT(s) for market surveillance While discharging its duties under the BIS Act 2016, BIS is committed to maintain the trust and respect of its stakeholders and the public at large through unquestionable integrity, honesty, behave profes

### guide_renewal (12 chunks): Guidelines for Renewal of Licence
- `guide_renewal::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:3 05 March 2025 Subject: Guidelines for Renewal of Licence (RoL) as per the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 This document stipulates the guidelines for ren
- `guide_renewal::0006` · p.1 · 2.  
  > 3) As per sub-regulation (5) of regulation 8 of the BIS (Conformity Assessment) Regulations, 2018, you may still submit the renewal application form along with requisite fee, accompanied with late fee of rupees five thousand, within ninety days from the last date of validity, i.e. upto .............
- `guide_renewal::0011` · p.1 · 2.  
  > upto .................... or suspension is not revoked upto one hundred and eighty days from the date of validity, then as per sub-regulation (7) and (9) of regulation 8 of the BIS (Conformity Assessment) Regulations, 2018 your licence has been expired after ............................. 4) As infor

### hm_jewellers_guidelines (12 chunks): Guidelines for Jewellers (Jul 2026)
- `hm_jewellers_guidelines::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (Hallmarking Department) 02.07.2026 [Our ref: HMD/14:7] Subject: Revised Guidelines for Grant, Operation, Surveillance & Cancellation of Certificate of Registration of Jeweller 1. This has reference to the Guidelines for Grant, Operation, Surveillance & Cancellation of Cer
- `hm_jewellers_guidelines::0006` · p.1 · (no section)  
  > from him that they abide to the observations made by the party present during the opening of counter sample. 4.25.6 In cases where counter sample could not be drawn due to insufficient weight of the article, the results of market sample report would be treated as final. 4.25.7 In any case, if there 
- `hm_jewellers_guidelines::0011` · p.23 · ANNEX C  
  > ANNEX C DOC: HM/JWLR/F 1.3 [January 2024] REQUEST FOR HALLMARKING a) Name & Address of the registered jeweller: b) Registration No. : Sl. No Type of article Nos Weight Declared Purity Remarks [c)] Name & Signature of Authorized Representative of Jeweller with date

### hm_faq_general (11 chunks): Hallmarking FAQ (general)
- `hm_faq_general::0000` · p.- · General  
  > # General 1.What is Hallmarking? Hallmarking is the accurate determination and official recording of the proportionate content of precious metal in precious metal articles (as per IS 15820). Hallmarks are thus official marks used in India as a guarantee of purity or fineness of precious metal articl
- `hm_faq_general::0005` · p.- · 12. Does Hallmark charges include making charges and wastage charges?  
  > 12. Does Hallmark charges include making charges and wastage charges? No. 13. Are the hallmarking charges dependent on weight of jewellery? No, hallmarking charges are paid per article irrespective of the weight of the article. 14. Is it necessary to take authentic bills/invoice for the hallmarked a
- `hm_faq_general::0010` · p.- · 25. Is it possible for the common man to get his/her hallmarked jewellery tested for purity from an A&H centre?  
  > 25. Is it possible for the common man to get his/her hallmarked jewellery tested for purity from an A&H centre? Yes, after paying testing charges of Rs. 200(for testing by fire assay method as per IS 1418) to any of BIS recognized A&H centre. The list of BIS recognized A&H centre is available at BIS

### guide_renewal_coc (10 chunks): Guidelines for Renewal of Certificate of Conformity (Scheme IV)
- `guide_renewal_coc::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:16:3 18 January 2022 Subject: Guidelines for renewal of Certificate of Conformity as per the conformity assessment Scheme – IV of Schedule – II of the BIS (Conformity Assessment) Regulations, 2018 This document stipulates the
- `guide_renewal_coc::0005` · p.3 · Annexure-I  
  > Annexure-I Subject: Provision of submission of renewal application with late fee within 90 days of validity - reg. [M/s] ( Kind Attn. Name of CEO/MD ) 1) This has reference to BIS Certificate of Conformity No. ……......... granted to you for your product ……............. under Scheme-IV of Schedule-II
- `guide_renewal_coc::0009` · p.8 · Annexure-V  
  > Annexure-V Subject : Expiry of BIS Certificate of Conformity No. ……… as per specified requirement(s) ……. - reg. [M/s] ( Kind Attn. Name of CEO/MD ) Dear Madam/Sir(s), 1) Please refer to our communication Ref: ............... dated ..................... regarding deferment of decision to renew BIS Ce

### fmcs_faq (9 chunks): FMCS FAQs
- `fmcs_faq::0000` · p.- · Frequently Asked Questions  
  > # Frequently Asked Questions 1 What is FMCS ? This is a certification scheme for a Foreign manufacturer who wants to obtain BIS Licence. The scheme is for certification of products other than Electronic and Information Technology Products. For Electronic and IT products please refer to Registration 
- `fmcs_faq::0004` · p.- · 10. Whether the test report as per IEC or any standard other than Indian Standard can be accepted?  
  > 10. Whether the test report as per IEC or any standard other than Indian Standard can be accepted? Not accepted , only the test report as per relevant Indian Standard only be accepted. 11. Whether the sample of the product drawn during inspection can be tested in any ILAC/APLAC approved lab or, any 
- `fmcs_faq::0008` · p.- · 20. For further queries please contact  
  > 20. For further queries please contact For further queries please contact Room No. 459, Manakalaya Building Bureau of Indian Standards, 9, Bahadur Shah Zafar Marg, New Delhi – 110002. Telephone: 011-2323 0131/3375/9402, 2360 8280/8319/8449 Email: fmcs[at]bis[dot]gov[dot]in

### guide_coc_surveillance (9 chunks): Guidelines for Surveillance under Scheme IV (Stampings/Laminations/Core of Transformers)
- `guide_coc_surveillance::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:16:6 23 July 2024 Subject: Guidelines for surveillance during operation of Certificate of Conformity for Stampings/ Laminations/cores of transformers (with or without winding) under the conformity assessment Scheme – IV of Sc
- `guide_coc_surveillance::0004` · p.1 · (no section)  
  > [M/s] Kind Attn: (Name of the CEO/MD) Dear Madam/Sir, 1) This has reference to the certificate of conformity No. ....................... granted by BIS under its conformity assessment Scheme-IV for ………………………… (Product name) which is valid up to ………………. 2) Further, reference is invited to discrepanci
- `guide_coc_surveillance::0008` · p.1 · (no section)  
  > …….... As already informed earlier as well, you are neither entitled to use this certificate of conformity after ……… or to claim in your advertisements or in any other publicity material that you are a holding certificate of conformity granted by BIS on your product after ………. 5) Any publicity mater

### application_checklist (8 chunks): Check-list for application to be submitted by applicant to BIS
- `application_checklist::0000` · p.1 · 1. Name  
  > CHECK-LIST FOR APPLICATION TO BE SUBMITTED BY APPLICANT TO BIS WHILE APPLYING FOR BIS LICENCE UNDER PRODUCT CERTIFICATION SCHEME OF BIS The following check-list is required to be submitted with all the applications for grant of BIS licence under the Product Certification Scheme of BIS. No. Check-poi
- `application_checklist::0004` · p.2 · 13. Test Report(s) a  
  > 13. Test Report(s) a. Is the attached test report of in-house or from independent laboratory cover all requirements of the Indian Standard and is passing in such requirements? b. In case the application is filed under “simplified Procedure” is the test report(s), in original, as submitted a) from BI
- `application_checklist::0007` · p.4 · 21. Agreement  
  > 21. Agreement Does the applicant agree to sign a legally binding agreement with BIS in the prescribed format? Does the applicant agree to submit an Indemnity Bond to BIS in the prescribed format? [22. Indemnity Bond] Does the applicant agree to furnish a Performance Bank Guarantee to BIS of US $ 100

### crs_standard_mark_guidelines (8 chunks): CRS Standard Mark Guidelines
- `crs_standard_mark_guidelines::0000` · p.1 · 1.  
  > BUREAU OF INDIAN STANDARDS (Registration Department) Our Ref: Registration/CRS E&IT & Solar Goods 06.09.2019 Subject: Marking requirement as per self-declaration of Conformity {Scheme-II of Schedule II of BIS (Conformity Assessment) Regulations, 2018} 1. BIS (Conformity Assessment) Regulations, 2018
- `crs_standard_mark_guidelines::0004` · p.4 · Annexure-II  
  > Annexure-II The IS number and licence number given above are examples only. Please also refer Gazette Notification S. O. 3240(E) dated 01 December 2015, for display of IS numbers for each product. Annexure-III Colour Scheme for the ‘Standard Mark’ CENTRAL MARKS DEPARTMENT-III Ref: CMD III/9:6/e-labe
- `crs_standard_mark_guidelines::0007` · p.6 · Annexure-III > 7. All the applicable regulatory information required on the packaging or user manual shall  
  > 7. All the applicable regulatory information required on the packaging or user manual shall be provided according to the applicable rules even if it is displayed electronically. 8. If the primary user manual or user guide is provided by other electronic media (e.g., CD or online access) this informa

### law_page (6 chunks): BIS Act, Rules & Regulations index page
- `law_page::0000` · p.- · BIS Act, Rules & Regulations  
  > # BIS Act, Rules & Regulations / S.No / Title / Size / Format / View / Download / / --- / --- / --- / --- / --- / --- / / 1 / BIS Act, 2016 / 133 kb / Pdf / [View](https://www.bis.gov.in/wp-content/uploads/2020/12/BIS-Act-2016.pdf "BIS Act, 2016") / [Download](https://www.bis.gov.in/wp-content/uploa
- `law_page::0003` · p.- · BIS Act, Rules & Regulations  
  > / 18 / BIS (Conformity Assessment) Fourth Amendment Regulations, 2021 / 1 MB / Pdf / [View](https://www.bis.gov.in/wp-content/uploads/2021/08/BIS-CA-4th-Amendment-Regulations-2021-Gazette.pdf "BIS (Conformity Assessment) Fourth Amendment Regulations, 2021") / [Download](https://www.bis.gov.in/wp-con
- `law_page::0005` · p.- · BIS Act, Rules & Regulations  
  > / 29 / Amendment to the Bureau of Indian Standards (Conformity Assessment) Regulation, 2026 / 2.3 MB / Pdf / [View](https://www.bis.gov.in/wp-content/uploads/2026/03/Gazette-Notification-1.pdf "Amendment to the Bureau of Indian Standards (Conformity Assessment) Regulation, 2026") / [Download](https:

### cert_faq (4 chunks): Product Certification FAQ
- `cert_faq::0000` · p.- · Frequently Asked Questions  
  > # Frequently Asked Questions Q 1 What is a licence? Licence means a licence granted under Section 13 of BIS Act 2016 to use a specified Standard Mark in relation to any goods or article which conforms to a standard. Q.2 I am a manufacturer of a product and interested in applying for BIS product cert
- `cert_faq::0002` · p.- · Frequently Asked Questions  
  > Conditions of BIS licence to use or apply a Standard Mark are as given in Regulation 6 of BIS (Conformity Assessment) Regulations, 2018 Q17. What are the punitive provisions for non-compliance with the conditions of the licence? In case of violation of conditions of licence, licence may be cancelled
- `cert_faq::0003` · p.- · Frequently Asked Questions  
  > However, you can get the scope of licence changed (inclusion or deletion of varieties) with reference to the standard against which licence has been granted and as per applicable relevant guidelines. For change in the existing scope of product licence (addition/ deletion of varieties), please visit:

### consumer_protection (4 chunks): Consumer protection
- `consumer_protection::0000` · p.- · Consumer Protection  
  > # Consumer Protection Complaints Management & Enforcement Department (CMED) at BIS HQ in New Delhi is working with Public Grievance Officers at all its Regional and Branch Offices to provide consumers with prompt attention and speedy redressal of their grievances/complaints. Grievance/Complaint can 
- `consumer_protection::0002` · p.- · 3. Violation of Quality Control Order  
  > 3. Violation of Quality Control Order * Provide complete address (with landmark) of the retailer/dealer/exhibitor where the violation is observed. * In case the product has been purchased, provide purchase details like cash memo, etc. * If known, indicate complete address (with landmark) of the unit
- `consumer_protection::0003` · p.- · 5. Services Related and Other Miscellaneous Complaints  
  > 5. Services Related and Other Miscellaneous Complaints * Indicate the name/type of services availed from BIS and also provide the specific details. * If applicable, provide a copy of the cash memo in case it is applicable.

### hm_faq_general__bis_act_and_regulation_faq (4 chunks): Hallmarking FAQ (general): BIS Act and Regulation
- `hm_faq_general__bis_act_and_regulation_faq::0000` · p.- · BIS Act and Regulation  
  > # BIS Act and Regulation 1. Is Hallmarking covered under BIS Act, 2016? Yes, Hallmarking is covered under BIS Act, 2016. 2. Are there any regulations for Hallmarking specified by the Government of India? Yes, BIS (Hallmarking) Regulations, 2018 which were notified on June 14, 2018 3. What aspects ar
- `hm_faq_general__bis_act_and_regulation_faq::0002` · p.- · 6. What are the terms and conditions under which registration/certification is granted to jewellers?  
  > 6. What are the terms and conditions under which registration/certification is granted to jewellers? Terms and conditions of certificate of registration are listed in regulation 5 under Chapter I of Hallmarking Regulations, 2018. Also refer to the Amendment to the Bureau of Indian Standards (Hallmar
- `hm_faq_general__bis_act_and_regulation_faq::0003` · p.- · 8. Can violation of terms and conditions lead to cancellation of Registration/certification of jewellers?  
  > 8. Can violation of terms and conditions lead to cancellation of Registration/certification of jewellers? Yes, the violation of terms and conditions may lead to the cancellation of the registration/certification. 9. Can violation of terms and conditions lead to cancellation of Recognition of AHCs? Y

### hm_faq_general__mandatory (4 chunks): Hallmarking FAQ (general): Consumers
- `hm_faq_general__mandatory::0000` · p.- · Consumers  
  > # Consumers 1. Can people sell their old jewellery to jewelers after Hallmarking becomes mandatory? A) Yes, Consumer can sell old un-hallmarked/hallmarked jewellery lying with them to the jewellers. 2. What is the provision of compensation to the consumer for any shortfall in purity of hallmarked ar
- `hm_faq_general__mandatory::0002` · p.- · 4. Who will decide the amount of compensation in cases of complaint of purity of the hallmarked article being lesser than declared/marked purity?  
  > 4. Who will decide the amount of compensation in cases of complaint of purity of the hallmarked article being lesser than declared/marked purity? The amount of compensation has already been specified in sub-rule(1) of Rule 49 of BIS Rules, 2018 which states “Provided that in case of precious metal a
- `hm_faq_general__mandatory::0003` · p.- · 6. How will customer identify jeweller’s name from the HUID?  
  > 6. How will customer identify jeweller’s name from the HUID? Customer can verify the HUID number in the BIS Care App using the ‘Verify HUID’ feature and get the information related to the jeweller’s registration no.

### cert_fee (3 chunks): Product Certification Fee
- `cert_fee::0000` · p.- · Fee  
  > # Fee * [Search Marking Fee for an Indian Standard](https://www.manakonline.in/MANAK/knowfees) * [Download Marking Fee for all Products Under Certification (Scheme-I) (size – 1102 KB)](https://www.bis.gov.in/wp-content/uploads/2026/09/Marking-fee-for-all-products-under-certification-scheme-1.pdf) * 
- `cert_fee::0001` · p.- · Fee  
  > (size – 1456 KB)](https://www.bis.gov.in/wp-content/uploads/2022/12/241346.pdf) * [Amendment to Notification of Marking Fee for use of Standard Mark dated 03.02.2023 (size – 667 KB)](https://www.bis.gov.in/wp-content/uploads/2023/02/243465.pdf) * [Amendment to Notification of Marking Fee for use of 
- `cert_fee::0002` · p.- · Fee  
  > * [Amendment to Notification of Marking Fee for use of Standard Mark dated 02.01.2026 (size -784 KB)](https://www.bis.gov.in/wp-content/uploads/2026/01/Notification.pdf) * [Fees concession extension for Scheme-I (size -784 KB)](https://www.bis.gov.in/wp-content/uploads/2026/03/Scheme-1-Concession-Ex

### hm_overview (3 chunks): Hallmarking overview
- `hm_overview::0000` · p.- · Hallmarking overview  
  > # Hallmarking overview Hallmarking is the accurate determination and official recording of the proportionate content of precious metal in precious metal articles. Hallmarks are thus official marks used in many countries as a guarantee of purity or fineness of precious metal articles. The principle o
- `hm_overview::0001` · p.- · Hallmarking overview  
  > [Read More »](https://www.bis.gov.in/index.php/hallmarking-overview/gold-monetization-scheme/) **1) Check testing of Hallmarked/Unhallmarked articles by Consumer:** * Consumer can get its jewellery/sample tested from any of the BIS Recognized Assaying & Hallmarking Centre. The Assaying and Hallmarki
- `hm_overview::0002` · p.- · What is Hallmarking?  
  > **1. What is Hallmarking?** Hallmarking is the accurate determination and official recording of the proportionate content of precious metal in precious metal articles. **2. What are the objectives behind instituting Hallmarking Scheme?** To protect consumer against victimization due to irregular gol

### guide_retesting (3 chunks): Guidelines for Sample Coding and Retesting of Samples
- `guide_retesting::0000` · p.1 · (no section)  
  > BUREAU OF INDIAN STANDARDS (CENTRAL MARKS DEPARTMENT - I) Our Ref: CMD-I/2:12:5 14 July 2025 Subject: Guidelines for coding and retesting of sample(s) for the conformity assessment Scheme – I of Schedule – II of BIS (Conformity Assessment) Regulations, 2018 This document stipulates the guidelines fo
- `guide_retesting::0001` · p.1 · (no section)  
  > representative shall be pasted on product and/or packaging, as feasible. In addition to signatures on codes, samples and/or packaging (wherever feasible) shall also be signed with date by both certification officer/agent and manufacturer’s representative ensuring durability of ink used. Wax seal sho
- `guide_retesting::0002` · p.1 · (no section)  
  > travel, boarding and lodging for the BIS official to witness the testing shall be payable by the manufacturer. The concerned officer incharge and QA officer shall also personally remain present and witness such testing either in BIS laboratory or BIS recognised/empanelled laboratory. 11) In case, th

### marking_requirements (3 chunks): Marking requirement as per BIS (CA) Regulations
- `marking_requirements::0000` · p.1 · Regulation 1.  
  > BUREAU OF INDIAN STANDARDS (Registration Department) Our Ref: Registration/CRS E&IT & Solar Goods 06.09.2019 Subject: Marking requirement as per self-declaration of Conformity {Scheme-II of Schedule II of BIS (Conformity Assessment) Regulations, 2018} 1. BIS (Conformity Assessment) Regulations, 2018
- `marking_requirements::0001` · p.1 · Regulation 2. The provision of e-labelling also exists for which guidelines as per circular  
  > 2. The provision of e-labelling also exists for which guidelines as per circular CMD-III/9:6/e-labelling dated 13.09.2017 have been issued. 3. In regard to marking of reference to BIS website, as per provision of para 6 (7) of Scheme II, the following is clarified: i) BIS website reference www.bis.g
- `marking_requirements::0002` · p.1 · Regulation 4. This circular supersedes all previous circulars other than above mentioned  
  > 4. This circular supersedes all previous circulars other than above mentioned circular on e-labelling. This issues with the approval of Competent Authority. Sd/- Nishat S. Haque Head (Registration)

### cert_overview (2 chunks): Product Certification Overview
- `cert_overview::0000` · p.- · Product Certification Overview  
  > # Product Certification Overview Indian Standards Institution (ISI) was established on 6 January 1947 as a Registered Society under the Societies Registration Act, 1860. Being the National Standards Body of India, the organization had a clear mandate of preparing and promoting Standards for adoption
- `cert_overview::0001` · p.- · What is the procedure for obtaining BIS licence?  
  > **1. What is the procedure for obtaining BIS licence?** Guidelines for Grant of licence for Certification Scheme – I **2. What is Indian Standard Number for my Product?** [Click here](https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails). **3. What is t

### fmcs_how_to_apply (2 chunks): FMCS How to Apply
- `fmcs_how_to_apply::0000` · p.- · How to apply  
  > # How to apply * Fill-up the prescribed [Application Form](https://www.bis.gov.in/wp-content/uploads/2019/04/Application-Form-V.pdf) alongwith [necessary documentation.](https://www.bis.gov.in/wp-content/uploads/2018/08/FM_CHECKLIST.pdf) * [Nominate an Authorized Indian Representative (AIR)](https:/
- `fmcs_how_to_apply::0001` · p.- · 2.  
  > 2. The applicant will be responsible for delay in grant of licence in case of submission of incomplete application; delay in response to queries raised, if any ; payment of dues, etc.*

### fmcs_overview (2 chunks): FMCS (Foreign Manufacturers) Overview
- `fmcs_overview::0000` · p.- · FMCS Overview  
  > # FMCS Overview * Bureau of Indian Standards (BIS) has been operating a Foreign Manufacturers Certification Scheme (FMCS) since the year 2000 under [BIS Act, 2016 and Rules & Regulations](https://www.bis.gov.in/index.php/the-bureau/bis-act-rules-and-regulations/) framed there under. * Under FMCS, li
- `fmcs_overview::0001` · p.- · Contact Details  
  > ## Contact Details Head (FMCD) Room No. 459, Manakalaya Building Bureau of Indian Standards, 9, Bahadur Shah Zafar Marg, New Delhi – 110002. **Telephone** : 011-2323 0131/3375/9402, 2360 8280/8319/8449 **Telefax** : 91 11 2323 9382 **Email** : fmcs[at]bis[dot]gov[dot]in

### hm_mandatory_order_page (2 chunks): Mandatory Hallmarking Order page
- `hm_mandatory_order_page::0000` · p.- · Mandatory Hallmarking Order  
  > # Mandatory Hallmarking Order * [Order (size – 467 KB)](https://www.bis.gov.in/wp-content/uploads/2020/01/Mandatory-Hallmarking-Order-15.01.2020.pdf "Order") * [Amendment dt 9th October 2020(size – 1423 KB)](https://www.bis.gov.in/wp-content/uploads/2020/10/Hallmarking-of-Gold-Jewellery-and-Gold-Art
- `hm_mandatory_order_page::0001` · p.- · Mandatory Hallmarking Order  
  > * [Amendment 28 April 2026.(size – 354 KB)](https://www.bis.gov.in/wp-content/uploads/2026/05/Hallmarking-of-gold-jewellery-and-gold-artefacts-order-2026-second-amendments-385-districts-1.pdf "Amendment 28 April 2026") * [Amendment 03 August 2026.(size – 354 KB)](https://www.bis.gov.in/wp-content/up

### hm_order_2020 (2 chunks): Hallmarking of Gold Jewellery and Gold Artefacts Order, 2020
- `hm_order_2020::0000` · p.1 · (no section)  
  > 33004/99 33004/99 33004/99 33004/99 33004/99 33004/99 ख ड (ii) . . . 195] No. 195] NEW DELHI, WEDESDAY, JANUARY 15, 2020/PAUSHA 25, 1941 286 GI/2020 MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION 1. (Department of Consumer Affairs) ORDER New Delhi, the 15th January, 2020 S.O. 205(E).—In
- `hm_order_2020::0001` · p.1 · (no section)  
  > 3. Certification and enforcing authority.—In respect of the goods and articles specified in column (2) of the Table, the Bureau of Indian Standards shall be the certifying and enforcing authority and an officer not below the rank of Joint Secretary of the Department having administrative control ove

### hm_regs_amdt_2026 (2 chunks): Hallmarking Amendment Regulations, 2026
- `hm_regs_amdt_2026::0000` · p.1 · (no section)  
  > No. 557] NEW DELHI, MONDAY, SEPTEMBER 14, 2026/BHADRA 23, 1948 (2) 7059 GI/2026 (1) (i) (ii) (i) (ii) (i) (ii) MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION (Department Of Consumer Affairs) (BUREAU OF INDIAN STANDARDS) NOTIFICATION New Delhi, the 14th September, 2026 F. No. BS/11/05/201
- `hm_regs_amdt_2026::0001` · p.3 · Regulation 2.  
  > 2. (a) The Hallmarking fee for silver articles payable to recognised Assaying and Hallmarking Centres by jewellers shall be : (i) Rs. 35/- per article; and (ii) minimum fee for a consignment as Rs. 150/-. (b) The Hallmarking fee to be levied by the Bureau from Assaying and Hallmarking Centre for sil

### cert_apply_online (1 chunks): Apply Online
- `cert_apply_online::0000` · p.- · Apply Online  
  > # Apply Online * [Click here to Apply Online](http://manakonline.in/)

### cert_process (1 chunks): Product Certification Process
- `cert_process::0000` · p.- · Product Certification Process  
  > # Product Certification Process [View Old guidelines](https://www.bis.gov.in/index.php/product-certification/product-certification-process-archives/?lang=en "View old guildelines") 1) [Scheme-I of BIS (Conformity Assessment) Regulations, 2018 (size – 7 MB)](https://www.bis.gov.in/wp-content/uploads/

### fmcs_fee (1 chunks): FMCS Fee
- `fmcs_fee::0000` · p.- · Fee  
  > # Fee * For details of Fee Structure, [Click here (size – 129 KB)](https://www.bis.gov.in/wp-content/uploads/2021/06/LIST-OF-FEE-3.pdf) * For details of Minimum Marking Fee (IS wise), [Click here](https://www.manakonline.in/MANAK/ApplicationLicenceRelatedrpt)

### bis_care_app_page (1 chunks): BIS apps (BIS CARE)
- `bis_care_app_page::0000` · p.- · BIS Care App  
  > ## BIS Care App Scan To Download BIS Care App [ ](https://www.bis.gov.in/wp-content/uploads/2025/03/PPT-BIS-Care-App-3.0-N3.mp4) BIS CARE Video

### consumer_complaint (1 chunks): Online complaint registration
- `consumer_complaint::0000` · p.- · Online Complaint Registration  
  > # Online Complaint Registration BIS follows a well-established complaint redressal procedure. Complaints are recorded centrally at Complaints Management and Enforcement Department (CMED). Complaints can be made both offline and online. Online complaint can be made through mobile app BIS CARE or by u

### crs_amdt_mar_2026 (1 chunks): CRS Order amendment S.O.1246(E), 10 Mar 2026
- `crs_amdt_mar_2026::0000` · p.1 · (no section)  
  > No. 1194] NEW DELHI, TUESDAY, MARCH 10, 2026/PHALGUNA 19, 1947 1723 GI/2026 (1) MINISTRY OF ELECTRONICS AND INFORMATION TECHNOLOGY ORDER New Delhi, the 10th March, 2026 S.O. 1246(E).— In exercise of the powers conferred by sub-section (1) and (2) of section 16 read with subsection (3) of section 25 

### ca_amdt_2026_corrigendum (1 chunks): Corrigendum to CA Amendment, 2026
- `ca_amdt_2026_corrigendum::0000` · p.1 · (no section)  
  > No. 303] NEW DELHI, THURSDAY, APRIL 30, 2026/ VAISAKHA 10, 1948 3077 GI/2026 (1) BUREAU OF INDIAN STANDARDS CORRIGENDUM New Delhi, the 28th April, 2026 F. No. BS/XI/11/01/2025-26.—The following correction is hereby made in the notification F. No. BS/XI/11/01/2025-26, the Bureau of Indian Standards (

## Documents with 0 chunks

56 documents (scanned without OCR, or only garbled Hindi):

- `crs_order_2021` (data/raw/pdf/certification/crs_order_2021.pdf): 14 pages without text
- `qco_16333` (data/raw/pdf/product_qco/qco_16333.pdf): 1 pages without text
- `qco_aniline` (data/raw/pdf/product_qco/qco_aniline.pdf): 2 pages without text
- `qco_corrigendum_direction_meat_milk_feed_30_01_2020` (data/raw/pdf/product_qco/qco_corrigendum_direction_meat_milk_feed_30_01_2020.pdf): 1 pages without text
- `qco_direction_meat_milk_feed_27_01_2020` (data/raw/pdf/product_qco/qco_direction_meat_milk_feed_27_01_2020.pdf): 1 pages without text
- `qco_electronics_and_information_technology_goods_requirement_of_compulsory_registration_order_2021_1` (data/raw/pdf/product_qco/qco_electronics_and_information_technology_goods_requirement_of_compulsory_registration_order_2021_1.pdf): 14 pages without text
- `qco_extension_of_timeline_for_compliance_with_the_direction_dated_27th_jan_2020_issued_under_16_5_of_food_safety_and_standards_act_2006` (data/raw/pdf/product_qco/qco_extension_of_timeline_for_compliance_with_the_direction_dated_27th_jan_2020_issued_under_16_5_of_food_safety_and_standards_act_2006.pdf): 2 pages without text
- `qco_extension_order` (data/raw/pdf/product_qco/qco_extension_order.pdf): 2 pages without text
- `qco_extension_order_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_1110_1990_and_is_4409_1973` (data/raw/pdf/product_qco/qco_extension_order_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_1110_1990_and_is_4409_1973.pdf): 2 pages without text
- `qco_extension_order_is_13387` (data/raw/pdf/product_qco/qco_extension_order_is_13387.pdf): 2 pages without text
- `qco_extension_order_is_14331` (data/raw/pdf/product_qco/qco_extension_order_is_14331.pdf): 2 pages without text
- `qco_extension_order_is_4409_dt_25_07_2023` (data/raw/pdf/product_qco/qco_extension_order_is_4409_dt_25_07_2023.pdf): 2 pages without text
- `qco_extension_oreder_of_is_4409` (data/raw/pdf/product_qco/qco_extension_oreder_of_is_4409.pdf): 3 pages without text
- `qco_extension_timeline_feeds_24_07_20202_1` (data/raw/pdf/product_qco/qco_extension_timeline_feeds_24_07_20202_1.pdf): 1 pages without text
- `qco_ferrocnickel_extension_quality_control_order_2024` (data/raw/pdf/product_qco/qco_ferrocnickel_extension_quality_control_order_2024.pdf): 2 pages without text
- `qco_gazette_notification_2012_10_03` (data/raw/pdf/product_qco/qco_gazette_notification_2012_10_03.pdf): 14 pages without text
- `qco_gsr_no_374e` (data/raw/pdf/product_qco/qco_gsr_no_374e.pdf): 2 pages without text
- `qco_gsr_no_843_e` (data/raw/pdf/product_qco/qco_gsr_no_843_e.pdf): 9 pages without text
- `qco_is_4409_2023_specification_for_ferronickel` (data/raw/pdf/product_qco/qco_is_4409_2023_specification_for_ferronickel.pdf): 2 pages without text
- `qco_jute_bags_quality_control_order_2022` (data/raw/pdf/product_qco/qco_jute_bags_quality_control_order_2022.pdf): 3 pages without text
- `qco_maleic_anhydride_qco_1` (data/raw/pdf/product_qco/qco_maleic_anhydride_qco_1.pdf): 2 pages without text
- `qco_medical_x_ray_qc_order` (data/raw/pdf/product_qco/qco_medical_x_ray_qc_order.pdf): 2 pages without text
- `qco_methanol` (data/raw/pdf/product_qco/qco_methanol.pdf): 2 pages without text
- `qco_ministry_of_steel_order_for_extension_of_date_of_implementation_is_1110_is_4409` (data/raw/pdf/product_qco/qco_ministry_of_steel_order_for_extension_of_date_of_implementation_is_1110_is_4409.pdf): 2 pages without text
- `qco_mnre_notification_published_in_gazette_on_12_10_2018` (data/raw/pdf/product_qco/qco_mnre_notification_published_in_gazette_on_12_10_2018.pdf): 4 pages without text
- `qco_order_for_extension_in_date_of_enforcement_for_is_1110_and_is_4409` (data/raw/pdf/product_qco/qco_order_for_extension_in_date_of_enforcement_for_is_1110_and_is_4409.pdf): 1 pages without text
- `qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order` (data/raw/pdf/product_qco/qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order.pdf): 1 pages without text
- `qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_4454_part_4_is_11946_is_11947` (data/raw/pdf/product_qco/qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_4454_part_4_is_11946_is_11947.pdf): 1 pages without text
- `qco_order_of_extension_in_the_enforcement_date_for_indian_standards_covered_under_the_quality_control_order_namely_is_3748_is_7291_and_is_12146` (data/raw/pdf/product_qco/qco_order_of_extension_in_the_enforcement_date_for_indian_standards_covered_under_the_quality_control_order_namely_is_3748_is_7291_and_is_12146.pdf): 1 pages without text
- `qco_order_of_extension_in_the_enforcement_date_for_some_indian_standards_covered_under_the_quality_control_order_namely_is_4398_and_is_3195` (data/raw/pdf/product_qco/qco_order_of_extension_in_the_enforcement_date_for_some_indian_standards_covered_under_the_quality_control_order_namely_is_4398_and_is_3195.pdf): 1 pages without text
- `qco_order_of_extension_in_the_enforcement_date_of_quality_control_order_for_tin_plate_and_tin_free_steel` (data/raw/pdf/product_qco/qco_order_of_extension_in_the_enforcement_date_of_quality_control_order_for_tin_plate_and_tin_free_steel.pdf): 1 pages without text
- `qco_ordero1` (data/raw/pdf/product_qco/qco_ordero1.pdf): 1 pages without text
- `qco_qco_extension_order_26042022` (data/raw/pdf/product_qco/qco_qco_extension_order_26042022.pdf): 1 pages without text
- `qco_qco_on_transparent_float_glass` (data/raw/pdf/product_qco/qco_qco_on_transparent_float_glass.pdf): 2 pages without text
- `qco_s_o_2434_e_electrical_capacitors_qco` (data/raw/pdf/product_qco/qco_s_o_2434_e_electrical_capacitors_qco.pdf): 6 pages without text
- `qco_so_178e` (data/raw/pdf/product_qco/qco_so_178e.pdf): 6 pages without text
- `qco_so_no_1057_e` (data/raw/pdf/product_qco/qco_so_no_1057_e.pdf): 2 pages without text
- `qco_so_no_1172_e` (data/raw/pdf/product_qco/qco_so_no_1172_e.pdf): 2 pages without text
- `qco_so_no_1221_e` (data/raw/pdf/product_qco/qco_so_no_1221_e.pdf): 5 pages without text
- `qco_so_no_165_e` (data/raw/pdf/product_qco/qco_so_no_165_e.pdf): 1 pages without text
- `qco_so_no_189_e` (data/raw/pdf/product_qco/qco_so_no_189_e.pdf): 7 pages without text
- `qco_so_no_191_e` (data/raw/pdf/product_qco/qco_so_no_191_e.pdf): 4 pages without text
- `qco_so_no_2033_e` (data/raw/pdf/product_qco/qco_so_no_2033_e.pdf): 2 pages without text
- `qco_so_no_2034_e` (data/raw/pdf/product_qco/qco_so_no_2034_e.pdf): 4 pages without text
- `qco_so_no_2058_e` (data/raw/pdf/product_qco/qco_so_no_2058_e.pdf): 1 pages without text
- `qco_so_no_2357_e` (data/raw/pdf/product_qco/qco_so_no_2357_e.pdf): 14 pages without text
- `qco_so_no_2578_e` (data/raw/pdf/product_qco/qco_so_no_2578_e.pdf): 5 pages without text
- `qco_so_no_2681_e` (data/raw/pdf/product_qco/qco_so_no_2681_e.pdf): 5 pages without text
- `qco_so_no_2749_e` (data/raw/pdf/product_qco/qco_so_no_2749_e.pdf): 7 pages without text
- `qco_so_no_2905_e` (data/raw/pdf/product_qco/qco_so_no_2905_e.pdf): 3 pages without text
- `qco_so_no_2953_e` (data/raw/pdf/product_qco/qco_so_no_2953_e.pdf): 10 pages without text
- `qco_so_no_451_e` (data/raw/pdf/product_qco/qco_so_no_451_e.pdf): 4 pages without text
- `qco_so_no_512_e` (data/raw/pdf/product_qco/qco_so_no_512_e.pdf): 1 pages without text
- `qco_so_no_822_e` (data/raw/pdf/product_qco/qco_so_no_822_e.pdf): 6 pages without text
- `qco_steel_qco_extension_order` (data/raw/pdf/product_qco/qco_steel_qco_extension_order.pdf): 1 pages without text
- `qco_transformerqco2014` (data/raw/pdf/product_qco/qco_transformerqco2014.pdf): 5 pages without text

## Pages with no text layer (need OCR)

265 pages in 61 documents:

- `crs_order_2021`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
- `ca_regulations_2018`: pages 242, 280, 281, 369, 370, 384, 385, 395, 396, 405, 406
- `qco_16333`: pages 1
- `qco_aniline`: pages 1, 2
- `qco_corrigendum_direction_meat_milk_feed_30_01_2020`: pages 1
- `qco_direction_meat_milk_feed_27_01_2020`: pages 1
- `qco_electronics_and_information_technology_goods_requirement_of_compulsory_registration_order_2021_1`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
- `qco_extension_of_timeline_for_compliance_with_the_direction_dated_27th_jan_2020_issued_under_16_5_of_food_safety_and_standards_act_2006`: pages 1, 2
- `qco_extension_order`: pages 1, 2
- `qco_extension_order_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_1110_1990_and_is_4409_1973`: pages 1, 2
- `qco_extension_order_is_13387`: pages 1, 2
- `qco_extension_order_is_14331`: pages 1, 2
- `qco_extension_order_is_4409_dt_25_07_2023`: pages 1, 2
- `qco_extension_oreder_of_is_4409`: pages 1, 2, 3
- `qco_extension_timeline_feeds_24_07_20202_1`: pages 1
- `qco_ferrocnickel_extension_quality_control_order_2024`: pages 1, 2
- `qco_gazette_notification_2012_10_03`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
- `qco_gsr_no_374e`: pages 1, 2
- `qco_gsr_no_759_e`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
- `qco_gsr_no_759_e_b64cf9`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
- `qco_gsr_no_759_e_dc3eaf`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
- `qco_gsr_no_760_e`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
- `qco_gsr_no_843_e`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9
- `qco_is_4409_2023_specification_for_ferronickel`: pages 1, 2
- `qco_jute_bags_quality_control_order_2022`: pages 1, 2, 3
- `qco_maleic_anhydride_qco_1`: pages 1, 2
- `qco_medical_x_ray_qc_order`: pages 1, 2
- `qco_methanol`: pages 1, 2
- `qco_ministry_of_steel_order_for_extension_of_date_of_implementation_is_1110_is_4409`: pages 1, 2
- `qco_mnre_notification_published_in_gazette_on_12_10_2018`: pages 1, 2, 3, 4
- `qco_order_for_extension_in_date_of_enforcement_for_is_1110_and_is_4409`: pages 1
- `qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order`: pages 1
- `qco_order_of_extension_in_the_date_of_enforcement_of_quality_control_order_for_indian_standards_is_4454_part_4_is_11946_is_11947`: pages 1
- `qco_order_of_extension_in_the_enforcement_date_for_indian_standards_covered_under_the_quality_control_order_namely_is_3748_is_7291_and_is_12146`: pages 1
- `qco_order_of_extension_in_the_enforcement_date_for_some_indian_standards_covered_under_the_quality_control_order_namely_is_4398_and_is_3195`: pages 1
- `qco_order_of_extension_in_the_enforcement_date_of_quality_control_order_for_tin_plate_and_tin_free_steel`: pages 1
- `qco_ordero1`: pages 1
- `qco_qco_extension_order_26042022`: pages 1
- `qco_qco_on_transparent_float_glass`: pages 1, 2
- `qco_s_o_2434_e_electrical_capacitors_qco`: pages 1, 2, 3, 4, 5, 6
- `qco_so_178e`: pages 1, 2, 3, 4, 5, 6
- `qco_so_no_1057_e`: pages 1, 2
- `qco_so_no_1172_e`: pages 1, 2
- `qco_so_no_1221_e`: pages 1, 2, 3, 4, 5
- `qco_so_no_165_e`: pages 1
- `qco_so_no_189_e`: pages 1, 2, 3, 4, 5, 6, 7
- `qco_so_no_191_e`: pages 1, 2, 3, 4
- `qco_so_no_2033_e`: pages 1, 2
- `qco_so_no_2034_e`: pages 1, 2, 3, 4
- `qco_so_no_2058_e`: pages 1
- `qco_so_no_2357_e`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
- `qco_so_no_2578_e`: pages 1, 2, 3, 4, 5
- `qco_so_no_2681_e`: pages 1, 2, 3, 4, 5
- `qco_so_no_2749_e`: pages 1, 2, 3, 4, 5, 6, 7
- `qco_so_no_2905_e`: pages 1, 2, 3
- `qco_so_no_2953_e`: pages 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
- `qco_so_no_451_e`: pages 1, 2, 3, 4
- `qco_so_no_512_e`: pages 1
- `qco_so_no_822_e`: pages 1, 2, 3, 4, 5, 6
- `qco_steel_qco_extension_order`: pages 1
- `qco_transformerqco2014`: pages 1, 2, 3, 4, 5
