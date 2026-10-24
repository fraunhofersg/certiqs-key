# Record excerpts

Every record value the key-rate report cites, once, under its JSON pointer (RFC 6901) from the record root, in the record's order. Report id 61556931d240d85fec512eb0190d727b19ab92bb75aba01b00d1a773c6a86119. [Back to the report](report.md)

## <a id="p-.payload.channel_interface.source_model"></a>/payload/channel_interface/source_model

`ideal_pair`

## <a id="p-.payload.channel_interface.source_shape"></a>/payload/channel_interface/source_shape

`bipartite`

## <a id="p-.payload.compiled"></a>/payload/compiled

| Field | Value |
| --- | --- |
| `public` | an object of 15 fields (27,426 characters); not shown, see the record |
| `source/alice_dim` | 1 |
| `source/alice_marginal` | — |
| `source/alice_povm/0` | 1 × 1 matrix: 1 |
| `source/public_choices` | — |
| `source/signal_alphabet` | x0 |
| `source/source_mode` | untrusted |
| `source/virtual_ensemble_weights/x0` | 1 |
| `source/virtual_transmitted_system` | 1 |

## <a id="p-.payload.compiled.public.choice_weightings"></a>/payload/compiled/public/choice_weightings

| Field | Value |
| --- | --- |
| `0/choice_alphabet` | gen, test |
| `0/factor` | alice_station |
| `0/matrix/off\|gen` | 7/8 |
| `0/matrix/off\|test` | 1/8 |
| `0/setting_alphabet` | off |
| `0/setting_map/A` | off |
| `0/setting_map/D` | off |
| `0/setting_map/H` | off |
| `0/setting_map/V` | off |
| `0/setting_map/mc` | off |
| `0/setting_map/nc` | off |
| `0/source_alphabet` | nc, H, V, D, A, mc |
| `0/support/0` | (nc,gen), nc, gen |
| `0/support/1` | (nc,test), nc, test |
| `0/support/2` | (H,gen), H, gen |
| `0/support/3` | (H,test), H, test |
| `0/support/4` | (V,gen), V, gen |
| `0/support/5` | (V,test), V, test |
| `0/support/6` | (D,gen), D, gen |
| `0/support/7` | (D,test), D, test |
| `0/support/8` | (A,gen), A, gen |
| `0/support/9` | (A,test), A, test |
| `0/support/10` | (mc,gen), mc, gen |
| `0/support/11` | (mc,test), mc, test |

## <a id="p-.payload.compiled.public.choice_weightings.0"></a>/payload/compiled/public/choice_weightings/0

| Field | Value |
| --- | --- |
| `choice_alphabet` | gen, test |
| `factor` | alice_station |
| `matrix/off\|gen` | 7/8 |
| `matrix/off\|test` | 1/8 |
| `setting_alphabet` | off |
| `setting_map/A` | off |
| `setting_map/D` | off |
| `setting_map/H` | off |
| `setting_map/V` | off |
| `setting_map/mc` | off |
| `setting_map/nc` | off |
| `source_alphabet` | nc, H, V, D, A, mc |
| `support/0` | (nc,gen), nc, gen |
| `support/1` | (nc,test), nc, test |
| `support/2` | (H,gen), H, gen |
| `support/3` | (H,test), H, test |
| `support/4` | (V,gen), V, gen |
| `support/5` | (V,test), V, test |
| `support/6` | (D,gen), D, gen |
| `support/7` | (D,test), D, test |
| `support/8` | (A,gen), A, gen |
| `support/9` | (A,test), A, test |
| `support/10` | (mc,gen), mc, gen |
| `support/11` | (mc,test), mc, test |

## <a id="p-.payload.compiled.public.key_holder"></a>/payload/compiled/public/key_holder

`B`

## <a id="p-.payload.compiled.public.key_map"></a>/payload/compiled/public/key_map

| Field | Value |
| --- | --- |
| `0/0` | x0, (nc,gen)\_\_nc |
| `0/1` | perp |
| `1/0` | x0, (nc,gen)\_\_H |
| `1/1` | perp |
| `2/0` | x0, (nc,gen)\_\_V |
| `2/1` | perp |
| `3/0` | x0, (nc,gen)\_\_D |
| `3/1` | perp |
| `4/0` | x0, (nc,gen)\_\_A |
| `4/1` | perp |
| `5/0` | x0, (nc,gen)\_\_mc |
| `5/1` | perp |
| `6/0` | x0, (nc,test)\_\_nc |
| `6/1` | perp |
| `7/0` | x0, (nc,test)\_\_H |
| `7/1` | perp |
| `8/0` | x0, (nc,test)\_\_V |
| `8/1` | perp |
| `9/0` | x0, (nc,test)\_\_D |
| `9/1` | perp |
| `10/0` | x0, (nc,test)\_\_A |
| `10/1` | perp |
| `11/0` | x0, (nc,test)\_\_mc |
| `11/1` | perp |
| `12/0` | x0, (H,gen)\_\_nc |
| `12/1` | perp |
| `13/0` | x0, (H,gen)\_\_H |
| `13/1` | 0 |
| `14/0` | x0, (H,gen)\_\_V |
| `14/1` | 1 |
| `15/0` | x0, (H,gen)\_\_D |
| `15/1` | perp |
| `16/0` | x0, (H,gen)\_\_A |
| `16/1` | perp |
| `17/0` | x0, (H,gen)\_\_mc |
| `17/1` | perp |
| `18/0` | x0, (H,test)\_\_nc |
| `18/1` | perp |
| `19/0` | x0, (H,test)\_\_H |
| `19/1` | perp |
| `20/0` | x0, (H,test)\_\_V |
| `20/1` | perp |
| `21/0` | x0, (H,test)\_\_D |
| `21/1` | perp |
| `22/0` | x0, (H,test)\_\_A |
| `22/1` | perp |
| `23/0` | x0, (H,test)\_\_mc |
| `23/1` | perp |
| `24/0` | x0, (V,gen)\_\_nc |
| `24/1` | perp |
| `25/0` | x0, (V,gen)\_\_H |
| `25/1` | 0 |
| `26/0` | x0, (V,gen)\_\_V |
| `26/1` | 1 |
| `27/0` | x0, (V,gen)\_\_D |
| `27/1` | perp |
| `28/0` | x0, (V,gen)\_\_A |
| `28/1` | perp |
| `29/0` | x0, (V,gen)\_\_mc |
| `29/1` | perp |
| `30/0` | x0, (V,test)\_\_nc |
| `30/1` | perp |
| `31/0` | x0, (V,test)\_\_H |
| `31/1` | perp |
| `32/0` | x0, (V,test)\_\_V |
| `32/1` | perp |
| `33/0` | x0, (V,test)\_\_D |
| `33/1` | perp |
| `34/0` | x0, (V,test)\_\_A |
| `34/1` | perp |
| `35/0` | x0, (V,test)\_\_mc |
| `35/1` | perp |
| `36/0` | x0, (D,gen)\_\_nc |
| `36/1` | perp |
| `37/0` | x0, (D,gen)\_\_H |
| `37/1` | perp |
| `38/0` | x0, (D,gen)\_\_V |
| `38/1` | perp |
| `39/0` | x0, (D,gen)\_\_D |
| `39/1` | 0 |
| `40/0` | x0, (D,gen)\_\_A |
| `40/1` | 1 |
| `41/0` | x0, (D,gen)\_\_mc |
| `41/1` | perp |
| `42/0` | x0, (D,test)\_\_nc |
| `42/1` | perp |
| `43/0` | x0, (D,test)\_\_H |
| `43/1` | perp |
| `44/0` | x0, (D,test)\_\_V |
| `44/1` | perp |
| `45/0` | x0, (D,test)\_\_D |
| `45/1` | perp |
| `46/0` | x0, (D,test)\_\_A |
| `46/1` | perp |
| `47/0` | x0, (D,test)\_\_mc |
| `47/1` | perp |
| `48/0` | x0, (A,gen)\_\_nc |
| `48/1` | perp |
| `49/0` | x0, (A,gen)\_\_H |
| `49/1` | perp |
| `50/0` | x0, (A,gen)\_\_V |
| `50/1` | perp |
| `51/0` | x0, (A,gen)\_\_D |
| `51/1` | 0 |
| `52/0` | x0, (A,gen)\_\_A |
| `52/1` | 1 |
| `53/0` | x0, (A,gen)\_\_mc |
| `53/1` | perp |
| `54/0` | x0, (A,test)\_\_nc |
| `54/1` | perp |
| `55/0` | x0, (A,test)\_\_H |
| `55/1` | perp |
| `56/0` | x0, (A,test)\_\_V |
| `56/1` | perp |
| `57/0` | x0, (A,test)\_\_D |
| `57/1` | perp |
| `58/0` | x0, (A,test)\_\_A |
| `58/1` | perp |
| `59/0` | x0, (A,test)\_\_mc |
| `59/1` | perp |
| `60/0` | x0, (mc,gen)\_\_nc |
| `60/1` | perp |
| `61/0` | x0, (mc,gen)\_\_H |
| `61/1` | perp |
| `62/0` | x0, (mc,gen)\_\_V |
| `62/1` | perp |
| `63/0` | x0, (mc,gen)\_\_D |
| `63/1` | perp |
| `64/0` | x0, (mc,gen)\_\_A |
| `64/1` | perp |
| `65/0` | x0, (mc,gen)\_\_mc |
| `65/1` | perp |
| `66/0` | x0, (mc,test)\_\_nc |
| `66/1` | perp |
| `67/0` | x0, (mc,test)\_\_H |
| `67/1` | perp |
| `68/0` | x0, (mc,test)\_\_V |
| `68/1` | perp |
| `69/0` | x0, (mc,test)\_\_D |
| `69/1` | perp |
| `70/0` | x0, (mc,test)\_\_A |
| `70/1` | perp |
| `71/0` | x0, (mc,test)\_\_mc |
| `71/1` | perp |

## <a id="p-.payload.compiled.public.transcript"></a>/payload/compiled/public/transcript

| Field | Value |
| --- | --- |
| `0/alphabet` | gen:Z, gen:X, gen:nc, gen:mc, test:nc, test:H, test:V, test:D, test:A, test:mc |
| `0/sender` | A |
| `0/table/0/0` | (nc,gen) |
| `0/table/0/1` | \[\] |
| `0/table/0/2` | gen:nc |
| `0/table/1/0` | (nc,test) |
| `0/table/1/1` | \[\] |
| `0/table/1/2` | test:nc |
| `0/table/2/0` | (H,gen) |
| `0/table/2/1` | \[\] |
| `0/table/2/2` | gen:Z |
| `0/table/3/0` | (H,test) |
| `0/table/3/1` | \[\] |
| `0/table/3/2` | test:H |
| `0/table/4/0` | (V,gen) |
| `0/table/4/1` | \[\] |
| `0/table/4/2` | gen:Z |
| `0/table/5/0` | (V,test) |
| `0/table/5/1` | \[\] |
| `0/table/5/2` | test:V |
| `0/table/6/0` | (D,gen) |
| `0/table/6/1` | \[\] |
| `0/table/6/2` | gen:X |
| `0/table/7/0` | (D,test) |
| `0/table/7/1` | \[\] |
| `0/table/7/2` | test:D |
| `0/table/8/0` | (A,gen) |
| `0/table/8/1` | \[\] |
| `0/table/8/2` | gen:X |
| `0/table/9/0` | (A,test) |
| `0/table/9/1` | \[\] |
| `0/table/9/2` | test:A |
| `0/table/10/0` | (mc,gen) |
| `0/table/10/1` | \[\] |
| `0/table/10/2` | gen:mc |
| `0/table/11/0` | (mc,test) |
| `0/table/11/1` | \[\] |
| `0/table/11/2` | test:mc |
| `1/alphabet` | Z, X, nc, mc, H, V, D, A |
| `1/sender` | B |
| `1/table/0/0` | nc |
| `1/table/0/1` | gen:Z |
| `1/table/0/2` | nc |
| `1/table/1/0` | nc |
| `1/table/1/1` | gen:X |
| `1/table/1/2` | nc |
| `1/table/2/0` | nc |
| `1/table/2/1` | gen:nc |
| `1/table/2/2` | nc |
| `1/table/3/0` | nc |
| `1/table/3/1` | gen:mc |
| `1/table/3/2` | nc |
| `1/table/4/0` | nc |
| `1/table/4/1` | test:nc |
| `1/table/4/2` | nc |
| `1/table/5/0` | nc |
| `1/table/5/1` | test:H |
| `1/table/5/2` | nc |
| `1/table/6/0` | nc |
| `1/table/6/1` | test:V |
| `1/table/6/2` | nc |
| `1/table/7/0` | nc |
| `1/table/7/1` | test:D |
| `1/table/7/2` | nc |
| `1/table/8/0` | nc |
| `1/table/8/1` | test:A |
| `1/table/8/2` | nc |
| `1/table/9/0` | nc |
| `1/table/9/1` | test:mc |
| `1/table/9/2` | nc |
| `1/table/10/0` | H |
| `1/table/10/1` | gen:Z |
| `1/table/10/2` | Z |
| `1/table/11/0` | H |
| `1/table/11/1` | gen:X |
| `1/table/11/2` | Z |
| `1/table/12/0` | H |
| `1/table/12/1` | gen:nc |
| `1/table/12/2` | Z |
| `1/table/13/0` | H |
| `1/table/13/1` | gen:mc |
| `1/table/13/2` | Z |
| `1/table/14/0` | H |
| `1/table/14/1` | test:nc |
| `1/table/14/2` | H |
| `1/table/15/0` | H |
| `1/table/15/1` | test:H |
| `1/table/15/2` | H |
| `1/table/16/0` | H |
| `1/table/16/1` | test:V |
| `1/table/16/2` | H |
| `1/table/17/0` | H |
| `1/table/17/1` | test:D |
| `1/table/17/2` | H |
| `1/table/18/0` | H |
| `1/table/18/1` | test:A |
| `1/table/18/2` | H |
| `1/table/19/0` | H |
| `1/table/19/1` | test:mc |
| `1/table/19/2` | H |
| `1/table/20/0` | V |
| `1/table/20/1` | gen:Z |
| `1/table/20/2` | Z |
| `1/table/21/0` | V |
| `1/table/21/1` | gen:X |
| `1/table/21/2` | Z |
| `1/table/22/0` | V |
| `1/table/22/1` | gen:nc |
| `1/table/22/2` | Z |
| `1/table/23/0` | V |
| `1/table/23/1` | gen:mc |
| `1/table/23/2` | Z |
| `1/table/24/0` | V |
| `1/table/24/1` | test:nc |
| `1/table/24/2` | V |
| `1/table/25/0` | V |
| `1/table/25/1` | test:H |
| `1/table/25/2` | V |
| `1/table/26/0` | V |
| `1/table/26/1` | test:V |
| `1/table/26/2` | V |
| `1/table/27/0` | V |
| `1/table/27/1` | test:D |
| `1/table/27/2` | V |
| `1/table/28/0` | V |
| `1/table/28/1` | test:A |
| `1/table/28/2` | V |
| `1/table/29/0` | V |
| `1/table/29/1` | test:mc |
| `1/table/29/2` | V |
| `1/table/30/0` | D |
| `1/table/30/1` | gen:Z |
| `1/table/30/2` | X |
| `1/table/31/0` | D |
| `1/table/31/1` | gen:X |
| `1/table/31/2` | X |
| `1/table/32/0` | D |
| `1/table/32/1` | gen:nc |
| `1/table/32/2` | X |
| `1/table/33/0` | D |
| `1/table/33/1` | gen:mc |
| `1/table/33/2` | X |
| `1/table/34/0` | D |
| `1/table/34/1` | test:nc |
| `1/table/34/2` | D |
| `1/table/35/0` | D |
| `1/table/35/1` | test:H |
| `1/table/35/2` | D |
| `1/table/36/0` | D |
| `1/table/36/1` | test:V |
| `1/table/36/2` | D |
| `1/table/37/0` | D |
| `1/table/37/1` | test:D |
| `1/table/37/2` | D |
| `1/table/38/0` | D |
| `1/table/38/1` | test:A |
| `1/table/38/2` | D |
| `1/table/39/0` | D |
| `1/table/39/1` | test:mc |
| `1/table/39/2` | D |
| `1/table/40/0` | A |
| `1/table/40/1` | gen:Z |
| `1/table/40/2` | X |
| `1/table/41/0` | A |
| `1/table/41/1` | gen:X |
| `1/table/41/2` | X |
| `1/table/42/0` | A |
| `1/table/42/1` | gen:nc |
| `1/table/42/2` | X |
| `1/table/43/0` | A |
| `1/table/43/1` | gen:mc |
| `1/table/43/2` | X |
| `1/table/44/0` | A |
| `1/table/44/1` | test:nc |
| `1/table/44/2` | A |
| `1/table/45/0` | A |
| `1/table/45/1` | test:H |
| `1/table/45/2` | A |
| `1/table/46/0` | A |
| `1/table/46/1` | test:V |
| `1/table/46/2` | A |
| `1/table/47/0` | A |
| `1/table/47/1` | test:D |
| `1/table/47/2` | A |
| `1/table/48/0` | A |
| `1/table/48/1` | test:A |
| `1/table/48/2` | A |
| `1/table/49/0` | A |
| `1/table/49/1` | test:mc |
| `1/table/49/2` | A |
| `1/table/50/0` | mc |
| `1/table/50/1` | gen:Z |
| `1/table/50/2` | mc |
| `1/table/51/0` | mc |
| `1/table/51/1` | gen:X |
| `1/table/51/2` | mc |
| `1/table/52/0` | mc |
| `1/table/52/1` | gen:nc |
| `1/table/52/2` | mc |
| `1/table/53/0` | mc |
| `1/table/53/1` | gen:mc |
| `1/table/53/2` | mc |
| `1/table/54/0` | mc |
| `1/table/54/1` | test:nc |
| `1/table/54/2` | mc |
| `1/table/55/0` | mc |
| `1/table/55/1` | test:H |
| `1/table/55/2` | mc |
| `1/table/56/0` | mc |
| `1/table/56/1` | test:V |
| `1/table/56/2` | mc |
| `1/table/57/0` | mc |
| `1/table/57/1` | test:D |
| `1/table/57/2` | mc |
| `1/table/58/0` | mc |
| `1/table/58/1` | test:A |
| `1/table/58/2` | mc |
| `1/table/59/0` | mc |
| `1/table/59/1` | test:mc |
| `1/table/59/2` | mc |

## <a id="p-.payload.compiled.source"></a>/payload/compiled/source

| Field | Value |
| --- | --- |
| `alice_dim` | 1 |
| `alice_marginal` | — |
| `alice_povm/0` | 1 × 1 matrix: 1 |
| `public_choices` | — |
| `signal_alphabet` | x0 |
| `source_mode` | untrusted |
| `virtual_ensemble_weights/x0` | 1 |
| `virtual_transmitted_system` | 1 |

## <a id="p-.payload.compiled.source.source_mode"></a>/payload/compiled/source/source_mode

`untrusted`

## <a id="p-.payload.config"></a>/payload/config

| Field | Value |
| --- | --- |
| `alpha` | — |
| `completeness_budget` | 1/1000000 |
| `config_digest` | 36f7e24cdc75605a8a0d476dc8d581e249b4c59141d33168983608a6033d2348 |
| `constrained` | — |
| `declared_tolerance` | 1e-12 |
| `device/acceptance_map` | pair-resolved |
| `device/alice_basis_split` | 1/2 |
| `device/alice_dark_count/A` | 0 |
| `device/alice_dark_count/D` | 0 |
| `device/alice_dark_count/H` | 0 |
| `device/alice_dark_count/V` | 0 |
| `device/alice_efficiency/A` | 1 |
| `device/alice_efficiency/D` | 1 |
| `device/alice_efficiency/H` | 1 |
| `device/alice_efficiency/V` | 1 |
| `device/alice_exact_window` | 2 |
| `device/alice_half_wave_angle` | 1/8 |
| `device/alice_pbs_leak_reflected` | 0 |
| `device/alice_pbs_leak_transmitted` | 0 |
| `device/alice_photon_cutoff` | 1 |
| `device/bob_basis_split` | 1/2 |
| `device/bob_dark_count/A` | 0 |
| `device/bob_dark_count/D` | 0 |
| `device/bob_dark_count/H` | 0 |
| `device/bob_dark_count/V` | 0 |
| `device/bob_efficiency/A` | 1 |
| `device/bob_efficiency/D` | 1 |
| `device/bob_efficiency/H` | 1 |
| `device/bob_efficiency/V` | 1 |
| `device/bob_exact_window` | 2 |
| `device/bob_half_wave_angle` | 1/8 |
| `device/bob_pbs_leak_reflected` | 0 |
| `device/bob_pbs_leak_transmitted` | 0 |
| `device/bob_photon_cutoff` | 1 |
| `device/key_bases` | ZX |
| `device/party_local_view` | operator |
| `device/route` | encoded |
| `device/source_model` | ideal_pair |
| `device/test_fraction` | 1/8 |
| `endpoint_rule` | bernstein |
| `model/alice_transmittance` | 1 |
| `model/bob_transmittance` | 1 |
| `model/mean_pairs` | 1/32 |
| `model/visibility` | 1 |
| `parameters/alpha` | 1.05 |
| `parameters/eps_auth` | 0.0 |
| `parameters/eps_ev` | 9.313225746154785e-10 |
| `parameters/eps_pa` | 9.313225746154785e-10 |
| `parameters/k_auth` | 0 |
| `parameters/lambda_ec` | 0 |
| `parameters/min_model_pass_probability` | 1/2 |
| `parameters/reference_enclosure` | true |
| `parameters/statistics_check` | on |
| `parameters/strict_snaps` | false |
| `rounds` | 100000000 |
| `solver/max_iterations` | 10 |
| `solver/method` | fw |
| `tail_evaluation` | sweep |

## <a id="p-.payload.config.alpha"></a>/payload/config/alpha

`—`

## <a id="p-.payload.config.completeness_budget"></a>/payload/config/completeness_budget

`1/1000000`

## <a id="p-.payload.config.constrained"></a>/payload/config/constrained

`—`

## <a id="p-.payload.config.declared_tolerance"></a>/payload/config/declared_tolerance

`1e-12`

## <a id="p-.payload.config.device.acceptance_map"></a>/payload/config/device/acceptance_map

`pair-resolved`

## <a id="p-.payload.config.device.alice_basis_split"></a>/payload/config/device/alice_basis_split

`1/2`

## <a id="p-.payload.config.device.alice_dark_count"></a>/payload/config/device/alice_dark_count

| Field | Value |
| --- | --- |
| `A` | 0 |
| `D` | 0 |
| `H` | 0 |
| `V` | 0 |

## <a id="p-.payload.config.device.alice_efficiency"></a>/payload/config/device/alice_efficiency

| Field | Value |
| --- | --- |
| `A` | 1 |
| `D` | 1 |
| `H` | 1 |
| `V` | 1 |

## <a id="p-.payload.config.device.alice_exact_window"></a>/payload/config/device/alice_exact_window

`2`

## <a id="p-.payload.config.device.alice_half_wave_angle"></a>/payload/config/device/alice_half_wave_angle

`1/8`

## <a id="p-.payload.config.device.alice_pbs_leak_reflected"></a>/payload/config/device/alice_pbs_leak_reflected

`0`

## <a id="p-.payload.config.device.alice_pbs_leak_transmitted"></a>/payload/config/device/alice_pbs_leak_transmitted

`0`

## <a id="p-.payload.config.device.alice_photon_cutoff"></a>/payload/config/device/alice_photon_cutoff

`1`

## <a id="p-.payload.config.device.bob_basis_split"></a>/payload/config/device/bob_basis_split

`1/2`

## <a id="p-.payload.config.device.bob_dark_count"></a>/payload/config/device/bob_dark_count

| Field | Value |
| --- | --- |
| `A` | 0 |
| `D` | 0 |
| `H` | 0 |
| `V` | 0 |

## <a id="p-.payload.config.device.bob_efficiency"></a>/payload/config/device/bob_efficiency

| Field | Value |
| --- | --- |
| `A` | 1 |
| `D` | 1 |
| `H` | 1 |
| `V` | 1 |

## <a id="p-.payload.config.device.bob_exact_window"></a>/payload/config/device/bob_exact_window

`2`

## <a id="p-.payload.config.device.bob_half_wave_angle"></a>/payload/config/device/bob_half_wave_angle

`1/8`

## <a id="p-.payload.config.device.bob_pbs_leak_reflected"></a>/payload/config/device/bob_pbs_leak_reflected

`0`

## <a id="p-.payload.config.device.bob_pbs_leak_transmitted"></a>/payload/config/device/bob_pbs_leak_transmitted

`0`

## <a id="p-.payload.config.device.bob_photon_cutoff"></a>/payload/config/device/bob_photon_cutoff

`1`

## <a id="p-.payload.config.device.key_bases"></a>/payload/config/device/key_bases

`ZX`

## <a id="p-.payload.config.device.party_local_view"></a>/payload/config/device/party_local_view

`operator`

## <a id="p-.payload.config.device.route"></a>/payload/config/device/route

`encoded`

## <a id="p-.payload.config.device.source_model"></a>/payload/config/device/source_model

`ideal_pair`

## <a id="p-.payload.config.device.test_fraction"></a>/payload/config/device/test_fraction

`1/8`

## <a id="p-.payload.config.endpoint_rule"></a>/payload/config/endpoint_rule

`bernstein`

## <a id="p-.payload.config.model.alice_transmittance"></a>/payload/config/model/alice_transmittance

`1`

## <a id="p-.payload.config.model.bob_transmittance"></a>/payload/config/model/bob_transmittance

`1`

## <a id="p-.payload.config.model.mean_pairs"></a>/payload/config/model/mean_pairs

`1/32`

## <a id="p-.payload.config.model.visibility"></a>/payload/config/model/visibility

`1`

## <a id="p-.payload.config.parameters"></a>/payload/config/parameters

| Field | Value |
| --- | --- |
| `alpha` | 1.05 |
| `eps_auth` | 0.0 |
| `eps_ev` | 9.313225746154785e-10 |
| `eps_pa` | 9.313225746154785e-10 |
| `k_auth` | 0 |
| `lambda_ec` | 0 |
| `min_model_pass_probability` | 1/2 |
| `reference_enclosure` | true |
| `statistics_check` | on |
| `strict_snaps` | false |

## <a id="p-.payload.config.parameters.alpha"></a>/payload/config/parameters/alpha

`1.05`

## <a id="p-.payload.config.parameters.eps_auth"></a>/payload/config/parameters/eps_auth

`0.0`

## <a id="p-.payload.config.parameters.eps_ev"></a>/payload/config/parameters/eps_ev

`9.313225746154785e-10`

## <a id="p-.payload.config.parameters.eps_pa"></a>/payload/config/parameters/eps_pa

`9.313225746154785e-10`

## <a id="p-.payload.config.parameters.k_auth"></a>/payload/config/parameters/k_auth

`0`

## <a id="p-.payload.config.parameters.lambda_ec"></a>/payload/config/parameters/lambda_ec

`0`

## <a id="p-.payload.config.parameters.min_model_pass_probability"></a>/payload/config/parameters/min_model_pass_probability

`1/2`

## <a id="p-.payload.config.parameters.reference_enclosure"></a>/payload/config/parameters/reference_enclosure

`true`

## <a id="p-.payload.config.parameters.statistics_check"></a>/payload/config/parameters/statistics_check

`on`

## <a id="p-.payload.config.parameters.strict_snaps"></a>/payload/config/parameters/strict_snaps

`false`

## <a id="p-.payload.config.rounds"></a>/payload/config/rounds

`100000000`

## <a id="p-.payload.config.solver.max_iterations"></a>/payload/config/solver/max_iterations

`10`

## <a id="p-.payload.config.solver.method"></a>/payload/config/solver/method

`fw`

## <a id="p-.payload.config.tail_evaluation"></a>/payload/config/tail_evaluation

`sweep`

## <a id="p-.payload.honest_model_note"></a>/payload/honest_model_note

| Field | Value |
| --- | --- |
| `model` | ideal_pair |
| `model_derivation` | instances/common/honest/pair_models.md |
| `overridden` | false |
| `source_trusted` | false |
| `status` | honest-data model; no source security attestation |

## <a id="p-.payload.instance.parameters.18.default"></a>/payload/instance/parameters/18/default

`—`

## <a id="p-.payload.instance.parameters.27.default"></a>/payload/instance/parameters/27/default

`—`

## <a id="p-.payload.snaps"></a>/payload/snaps

| Field | Value |
| --- | --- |
| `declared_tolerance` | 1e-12 |
| `instance` | an object of 2 fields (12,544 characters); not shown, see the record |
| `producer` | — |
| `reference_companion` | an object of 11 fields (5,699 characters); not shown, see the record |
| `snap_max_defect` | — |
| `snap_max_displacement` | 0.0 |

## <a id="p-.payload.snaps.instance.input_preparation"></a>/payload/snaps/instance/input_preparation

| Field | Value |
| --- | --- |
| `0/admission` | declared_tolerance |
| `0/binary64_values` | 7/8, 1/8 |
| `0/conversion_displacement` | 0, 0 |
| `0/declared_tolerance` | 1e-12 |
| `0/input_types` | Fraction, Fraction |
| `0/input_values` | 7/8, 1/8 |
| `0/lattice_exponent` | 12 |
| `0/normalization_defect` | 0 |
| `0/normalization_interval` | 1, 1 |
| `0/prepared_values` | 7/8, 1/8 |
| `0/representation_admitted` | true |
| `0/representation_policy` | binary64_nearest_even_cells_v1 |
| `0/rounding_cells/0/endpoints_closed` | true |
| `0/rounding_cells/0/lower` | 7/8 |
| `0/rounding_cells/0/upper` | 7/8 |
| `0/rounding_cells/1/endpoints_closed` | true |
| `0/rounding_cells/1/lower` | 1/8 |
| `0/rounding_cells/1/upper` | 1/8 |
| `0/rule` | shared_family_snap |
| `0/shared_snap_guard` | 1e-12 |
| `0/site` | bbm92.test_coin |
| `0/snaps` | \[\] |
| `0/total_displacement` | 0, 0 |

## <a id="p-.payload.stages.acceptance_construction"></a>/payload/stages/acceptance_construction

| Field | Value |
| --- | --- |
| `box/gen/lower` | 43719511/100000000 |
| `box/gen/upper` | 43780489/100000000 |
| `box/gen:X\|A/lower` | 0 |
| `box/gen:X\|A/upper` | 0 |
| `box/gen:X\|D/lower` | 0 |
| `box/gen:X\|D/upper` | 0 |
| `box/gen:X\|H/lower` | 0 |
| `box/gen:X\|H/upper` | 0 |
| `box/gen:X\|V/lower` | 0 |
| `box/gen:X\|V/upper` | 0 |
| `box/gen:X\|Z/lower` | 21849591/100000000 |
| `box/gen:X\|Z/upper` | 21900409/100000000 |
| `box/gen:X\|mc/lower` | 0 |
| `box/gen:X\|mc/upper` | 0 |
| `box/gen:X\|nc/lower` | 0 |
| `box/gen:X\|nc/upper` | 0 |
| `box/gen:Z\|A/lower` | 0 |
| `box/gen:Z\|A/upper` | 0 |
| `box/gen:Z\|D/lower` | 0 |
| `box/gen:Z\|D/upper` | 0 |
| `box/gen:Z\|H/lower` | 0 |
| `box/gen:Z\|H/upper` | 0 |
| `box/gen:Z\|V/lower` | 0 |
| `box/gen:Z\|V/upper` | 0 |
| `box/gen:Z\|X/lower` | 21849591/100000000 |
| `box/gen:Z\|X/upper` | 21900409/100000000 |
| `box/gen:Z\|mc/lower` | 0 |
| `box/gen:Z\|mc/upper` | 0 |
| `box/gen:Z\|nc/lower` | 0 |
| `box/gen:Z\|nc/upper` | 0 |
| `box/gen:mc\|A/lower` | 0 |
| `box/gen:mc\|A/upper` | 0 |
| `box/gen:mc\|D/lower` | 0 |
| `box/gen:mc\|D/upper` | 0 |
| `box/gen:mc\|H/lower` | 0 |
| `box/gen:mc\|H/upper` | 0 |
| `box/gen:mc\|V/lower` | 0 |
| `box/gen:mc\|V/upper` | 0 |
| `box/gen:mc\|X/lower` | 0 |
| `box/gen:mc\|X/upper` | 0 |
| `box/gen:mc\|Z/lower` | 0 |
| `box/gen:mc\|Z/upper` | 0 |
| `box/gen:mc\|mc/lower` | 0 |
| `box/gen:mc\|mc/upper` | 0 |
| `box/gen:mc\|nc/lower` | 0 |
| `box/gen:mc\|nc/upper` | 0 |
| `box/gen:nc\|A/lower` | 0 |
| `box/gen:nc\|A/upper` | 0 |
| `box/gen:nc\|D/lower` | 0 |
| `box/gen:nc\|D/upper` | 0 |
| `box/gen:nc\|H/lower` | 0 |
| `box/gen:nc\|H/upper` | 0 |
| `box/gen:nc\|V/lower` | 0 |
| `box/gen:nc\|V/upper` | 0 |
| `box/gen:nc\|X/lower` | 0 |
| `box/gen:nc\|X/upper` | 0 |
| `box/gen:nc\|Z/lower` | 0 |
| `box/gen:nc\|Z/upper` | 0 |
| `box/gen:nc\|mc/lower` | 0 |
| `box/gen:nc\|mc/upper` | 0 |
| `box/gen:nc\|nc/lower` | 0 |
| `box/gen:nc\|nc/upper` | 0 |
| `box/test:A\|A/lower` | 1554873/100000000 |
| `box/test:A\|A/upper` | 1570127/100000000 |
| `box/test:A\|D/lower` | 0 |
| `box/test:A\|D/upper` | 0 |
| `box/test:A\|H/lower` | 775833/100000000 |
| `box/test:A\|H/upper` | 786667/100000000 |
| `box/test:A\|V/lower` | 775833/100000000 |
| `box/test:A\|V/upper` | 786667/100000000 |
| `box/test:A\|X/lower` | 0 |
| `box/test:A\|X/upper` | 0 |
| `box/test:A\|Z/lower` | 0 |
| `box/test:A\|Z/upper` | 0 |
| `box/test:A\|mc/lower` | 0 |
| `box/test:A\|mc/upper` | 0 |
| `box/test:A\|nc/lower` | 0 |
| `box/test:A\|nc/upper` | 0 |
| `box/test:D\|A/lower` | 0 |
| `box/test:D\|A/upper` | 0 |
| `box/test:D\|D/lower` | 1554873/100000000 |
| `box/test:D\|D/upper` | 1570127/100000000 |
| `box/test:D\|H/lower` | 775833/100000000 |
| `box/test:D\|H/upper` | 786667/100000000 |
| `box/test:D\|V/lower` | 775833/100000000 |
| `box/test:D\|V/upper` | 786667/100000000 |
| `box/test:D\|X/lower` | 0 |
| `box/test:D\|X/upper` | 0 |
| `box/test:D\|Z/lower` | 0 |
| `box/test:D\|Z/upper` | 0 |
| `box/test:D\|mc/lower` | 0 |
| `box/test:D\|mc/upper` | 0 |
| `box/test:D\|nc/lower` | 0 |
| `box/test:D\|nc/upper` | 0 |
| `box/test:H\|A/lower` | 775833/100000000 |
| `box/test:H\|A/upper` | 786667/100000000 |
| `box/test:H\|D/lower` | 775833/100000000 |
| `box/test:H\|D/upper` | 786667/100000000 |
| `box/test:H\|H/lower` | 1554873/100000000 |
| `box/test:H\|H/upper` | 1570127/100000000 |
| `box/test:H\|V/lower` | 0 |
| `box/test:H\|V/upper` | 0 |
| `box/test:H\|X/lower` | 0 |
| `box/test:H\|X/upper` | 0 |
| `box/test:H\|Z/lower` | 0 |
| `box/test:H\|Z/upper` | 0 |
| `box/test:H\|mc/lower` | 0 |
| `box/test:H\|mc/upper` | 0 |
| `box/test:H\|nc/lower` | 0 |
| `box/test:H\|nc/upper` | 0 |
| `box/test:V\|A/lower` | 775833/100000000 |
| `box/test:V\|A/upper` | 786667/100000000 |
| `box/test:V\|D/lower` | 775833/100000000 |
| `box/test:V\|D/upper` | 786667/100000000 |
| `box/test:V\|H/lower` | 0 |
| `box/test:V\|H/upper` | 0 |
| `box/test:V\|V/lower` | 1554873/100000000 |
| `box/test:V\|V/upper` | 1570127/100000000 |
| `box/test:V\|X/lower` | 0 |
| `box/test:V\|X/upper` | 0 |
| `box/test:V\|Z/lower` | 0 |
| `box/test:V\|Z/upper` | 0 |
| `box/test:V\|mc/lower` | 0 |
| `box/test:V\|mc/upper` | 0 |
| `box/test:V\|nc/lower` | 0 |
| `box/test:V\|nc/upper` | 0 |
| `box/test:mc\|A/lower` | 0 |
| `box/test:mc\|A/upper` | 0 |
| `box/test:mc\|D/lower` | 0 |
| `box/test:mc\|D/upper` | 0 |
| `box/test:mc\|H/lower` | 0 |
| `box/test:mc\|H/upper` | 0 |
| `box/test:mc\|V/lower` | 0 |
| `box/test:mc\|V/upper` | 0 |
| `box/test:mc\|X/lower` | 0 |
| `box/test:mc\|X/upper` | 0 |
| `box/test:mc\|Z/lower` | 0 |
| `box/test:mc\|Z/upper` | 0 |
| `box/test:mc\|mc/lower` | 0 |
| `box/test:mc\|mc/upper` | 0 |
| `box/test:mc\|nc/lower` | 0 |
| `box/test:mc\|nc/upper` | 0 |
| `box/test:nc\|A/lower` | 0 |
| `box/test:nc\|A/upper` | 0 |
| `box/test:nc\|D/lower` | 0 |
| `box/test:nc\|D/upper` | 0 |
| `box/test:nc\|H/lower` | 0 |
| `box/test:nc\|H/upper` | 0 |
| `box/test:nc\|V/lower` | 0 |
| `box/test:nc\|V/upper` | 0 |
| `box/test:nc\|X/lower` | 0 |
| `box/test:nc\|X/upper` | 0 |
| `box/test:nc\|Z/lower` | 0 |
| `box/test:nc\|Z/upper` | 0 |
| `box/test:nc\|mc/lower` | 0 |
| `box/test:nc\|mc/upper` | 0 |
| `box/test:nc\|nc/lower` | 0 |
| `box/test:nc\|nc/upper` | 0 |
| `completeness_certified` | 1/1000000 |
| `completeness_exact` | false |
| `endpoint_rule` | bernstein |
| `geometry` | PolytopeGeometry |
| `honest_distribution/gen` | 7/16 |
| `honest_distribution/gen:X\|A` | 0 |
| `honest_distribution/gen:X\|D` | 0 |
| `honest_distribution/gen:X\|H` | 0 |
| `honest_distribution/gen:X\|V` | 0 |
| `honest_distribution/gen:X\|Z` | 7/32 |
| `honest_distribution/gen:X\|mc` | 0 |
| `honest_distribution/gen:X\|nc` | 0 |
| `honest_distribution/gen:Z\|A` | 0 |
| `honest_distribution/gen:Z\|D` | 0 |
| `honest_distribution/gen:Z\|H` | 0 |
| `honest_distribution/gen:Z\|V` | 0 |
| `honest_distribution/gen:Z\|X` | 7/32 |
| `honest_distribution/gen:Z\|mc` | 0 |
| `honest_distribution/gen:Z\|nc` | 0 |
| `honest_distribution/gen:mc\|A` | 0 |
| `honest_distribution/gen:mc\|D` | 0 |
| `honest_distribution/gen:mc\|H` | 0 |
| `honest_distribution/gen:mc\|V` | 0 |
| `honest_distribution/gen:mc\|X` | 0 |
| `honest_distribution/gen:mc\|Z` | 0 |
| `honest_distribution/gen:mc\|mc` | 0 |
| `honest_distribution/gen:mc\|nc` | 0 |
| `honest_distribution/gen:nc\|A` | 0 |
| `honest_distribution/gen:nc\|D` | 0 |
| `honest_distribution/gen:nc\|H` | 0 |
| `honest_distribution/gen:nc\|V` | 0 |
| `honest_distribution/gen:nc\|X` | 0 |
| `honest_distribution/gen:nc\|Z` | 0 |
| `honest_distribution/gen:nc\|mc` | 0 |
| `honest_distribution/gen:nc\|nc` | 0 |
| `honest_distribution/test:A\|A` | 1/64 |
| `honest_distribution/test:A\|D` | 0 |
| `honest_distribution/test:A\|H` | 1/128 |
| `honest_distribution/test:A\|V` | 1/128 |
| `honest_distribution/test:A\|X` | 0 |
| `honest_distribution/test:A\|Z` | 0 |
| `honest_distribution/test:A\|mc` | 0 |
| `honest_distribution/test:A\|nc` | 0 |
| `honest_distribution/test:D\|A` | 0 |
| `honest_distribution/test:D\|D` | 1/64 |
| `honest_distribution/test:D\|H` | 1/128 |
| `honest_distribution/test:D\|V` | 1/128 |
| `honest_distribution/test:D\|X` | 0 |
| `honest_distribution/test:D\|Z` | 0 |
| `honest_distribution/test:D\|mc` | 0 |
| `honest_distribution/test:D\|nc` | 0 |
| `honest_distribution/test:H\|A` | 1/128 |
| `honest_distribution/test:H\|D` | 1/128 |
| `honest_distribution/test:H\|H` | 1/64 |
| `honest_distribution/test:H\|V` | 0 |
| `honest_distribution/test:H\|X` | 0 |
| `honest_distribution/test:H\|Z` | 0 |
| `honest_distribution/test:H\|mc` | 0 |
| `honest_distribution/test:H\|nc` | 0 |
| `honest_distribution/test:V\|A` | 1/128 |
| `honest_distribution/test:V\|D` | 1/128 |
| `honest_distribution/test:V\|H` | 0 |
| `honest_distribution/test:V\|V` | 1/64 |
| `honest_distribution/test:V\|X` | 0 |
| `honest_distribution/test:V\|Z` | 0 |
| `honest_distribution/test:V\|mc` | 0 |
| `honest_distribution/test:V\|nc` | 0 |
| `honest_distribution/test:mc\|A` | 0 |
| `honest_distribution/test:mc\|D` | 0 |
| `honest_distribution/test:mc\|H` | 0 |
| `honest_distribution/test:mc\|V` | 0 |
| `honest_distribution/test:mc\|X` | 0 |
| `honest_distribution/test:mc\|Z` | 0 |
| `honest_distribution/test:mc\|mc` | 0 |
| `honest_distribution/test:mc\|nc` | 0 |
| `honest_distribution/test:nc\|A` | 0 |
| `honest_distribution/test:nc\|D` | 0 |
| `honest_distribution/test:nc\|H` | 0 |
| `honest_distribution/test:nc\|V` | 0 |
| `honest_distribution/test:nc\|X` | 0 |
| `honest_distribution/test:nc\|Z` | 0 |
| `honest_distribution/test:nc\|mc` | 0 |
| `honest_distribution/test:nc\|nc` | 0 |
| `outcomes` | gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:Z\|H, gen:Z\|V, gen:Z\|D, gen:Z\|A, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:X\|H, gen:X\|V, gen:X\|D, gen:X\|A, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:nc\|H, gen:nc\|V, gen:nc\|D, gen:nc\|A, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, gen:mc\|H, gen:mc\|V, gen:mc\|D, gen:mc\|A, test:nc\|Z, test:nc\|X, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|Z, test:H\|X, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|Z, test:V\|X, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|Z, test:D\|X, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|Z, test:A\|X, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|Z, test:mc\|X, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A |
| `raw_joint_distribution/x0\|(A,gen)__A` | 7/64 |
| `raw_joint_distribution/x0\|(A,gen)__D` | 0 |
| `raw_joint_distribution/x0\|(A,gen)__H` | 7/128 |
| `raw_joint_distribution/x0\|(A,gen)__V` | 7/128 |
| `raw_joint_distribution/x0\|(A,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(A,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(A,test)__A` | 1/64 |
| `raw_joint_distribution/x0\|(A,test)__D` | 0 |
| `raw_joint_distribution/x0\|(A,test)__H` | 1/128 |
| `raw_joint_distribution/x0\|(A,test)__V` | 1/128 |
| `raw_joint_distribution/x0\|(A,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(A,test)__nc` | 0 |
| `raw_joint_distribution/x0\|(D,gen)__A` | 0 |
| `raw_joint_distribution/x0\|(D,gen)__D` | 7/64 |
| `raw_joint_distribution/x0\|(D,gen)__H` | 7/128 |
| `raw_joint_distribution/x0\|(D,gen)__V` | 7/128 |
| `raw_joint_distribution/x0\|(D,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(D,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(D,test)__A` | 0 |
| `raw_joint_distribution/x0\|(D,test)__D` | 1/64 |
| `raw_joint_distribution/x0\|(D,test)__H` | 1/128 |
| `raw_joint_distribution/x0\|(D,test)__V` | 1/128 |
| `raw_joint_distribution/x0\|(D,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(D,test)__nc` | 0 |
| `raw_joint_distribution/x0\|(H,gen)__A` | 7/128 |
| `raw_joint_distribution/x0\|(H,gen)__D` | 7/128 |
| `raw_joint_distribution/x0\|(H,gen)__H` | 7/64 |
| `raw_joint_distribution/x0\|(H,gen)__V` | 0 |
| `raw_joint_distribution/x0\|(H,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(H,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(H,test)__A` | 1/128 |
| `raw_joint_distribution/x0\|(H,test)__D` | 1/128 |
| `raw_joint_distribution/x0\|(H,test)__H` | 1/64 |
| `raw_joint_distribution/x0\|(H,test)__V` | 0 |
| `raw_joint_distribution/x0\|(H,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(H,test)__nc` | 0 |
| `raw_joint_distribution/x0\|(V,gen)__A` | 7/128 |
| `raw_joint_distribution/x0\|(V,gen)__D` | 7/128 |
| `raw_joint_distribution/x0\|(V,gen)__H` | 0 |
| `raw_joint_distribution/x0\|(V,gen)__V` | 7/64 |
| `raw_joint_distribution/x0\|(V,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(V,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(V,test)__A` | 1/128 |
| `raw_joint_distribution/x0\|(V,test)__D` | 1/128 |
| `raw_joint_distribution/x0\|(V,test)__H` | 0 |
| `raw_joint_distribution/x0\|(V,test)__V` | 1/64 |
| `raw_joint_distribution/x0\|(V,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(V,test)__nc` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__A` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__D` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__H` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__V` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(mc,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__A` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__D` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__H` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__V` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(mc,test)__nc` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__A` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__D` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__H` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__V` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__mc` | 0 |
| `raw_joint_distribution/x0\|(nc,gen)__nc` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__A` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__D` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__H` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__V` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__mc` | 0 |
| `raw_joint_distribution/x0\|(nc,test)__nc` | 0 |
| `refused` | false |
| `support` | gen, gen:Z\|X, gen:X\|Z, test:H\|H, test:H\|D, test:H\|A, test:V\|V, test:V\|D, test:V\|A, test:D\|H, test:D\|V, test:D\|D, test:A\|H, test:A\|V, test:A\|A |
| `tail_evaluation` | sweep |

## <a id="p-.payload.stages.acceptance_construction.geometry"></a>/payload/stages/acceptance_construction/geometry

`PolytopeGeometry`

## <a id="p-.payload.stages.acceptance_construction.honest_distribution"></a>/payload/stages/acceptance_construction/honest_distribution

| Field | Value |
| --- | --- |
| `gen` | 7/16 |
| `gen:X\|A` | 0 |
| `gen:X\|D` | 0 |
| `gen:X\|H` | 0 |
| `gen:X\|V` | 0 |
| `gen:X\|Z` | 7/32 |
| `gen:X\|mc` | 0 |
| `gen:X\|nc` | 0 |
| `gen:Z\|A` | 0 |
| `gen:Z\|D` | 0 |
| `gen:Z\|H` | 0 |
| `gen:Z\|V` | 0 |
| `gen:Z\|X` | 7/32 |
| `gen:Z\|mc` | 0 |
| `gen:Z\|nc` | 0 |
| `gen:mc\|A` | 0 |
| `gen:mc\|D` | 0 |
| `gen:mc\|H` | 0 |
| `gen:mc\|V` | 0 |
| `gen:mc\|X` | 0 |
| `gen:mc\|Z` | 0 |
| `gen:mc\|mc` | 0 |
| `gen:mc\|nc` | 0 |
| `gen:nc\|A` | 0 |
| `gen:nc\|D` | 0 |
| `gen:nc\|H` | 0 |
| `gen:nc\|V` | 0 |
| `gen:nc\|X` | 0 |
| `gen:nc\|Z` | 0 |
| `gen:nc\|mc` | 0 |
| `gen:nc\|nc` | 0 |
| `test:A\|A` | 1/64 |
| `test:A\|D` | 0 |
| `test:A\|H` | 1/128 |
| `test:A\|V` | 1/128 |
| `test:A\|X` | 0 |
| `test:A\|Z` | 0 |
| `test:A\|mc` | 0 |
| `test:A\|nc` | 0 |
| `test:D\|A` | 0 |
| `test:D\|D` | 1/64 |
| `test:D\|H` | 1/128 |
| `test:D\|V` | 1/128 |
| `test:D\|X` | 0 |
| `test:D\|Z` | 0 |
| `test:D\|mc` | 0 |
| `test:D\|nc` | 0 |
| `test:H\|A` | 1/128 |
| `test:H\|D` | 1/128 |
| `test:H\|H` | 1/64 |
| `test:H\|V` | 0 |
| `test:H\|X` | 0 |
| `test:H\|Z` | 0 |
| `test:H\|mc` | 0 |
| `test:H\|nc` | 0 |
| `test:V\|A` | 1/128 |
| `test:V\|D` | 1/128 |
| `test:V\|H` | 0 |
| `test:V\|V` | 1/64 |
| `test:V\|X` | 0 |
| `test:V\|Z` | 0 |
| `test:V\|mc` | 0 |
| `test:V\|nc` | 0 |
| `test:mc\|A` | 0 |
| `test:mc\|D` | 0 |
| `test:mc\|H` | 0 |
| `test:mc\|V` | 0 |
| `test:mc\|X` | 0 |
| `test:mc\|Z` | 0 |
| `test:mc\|mc` | 0 |
| `test:mc\|nc` | 0 |
| `test:nc\|A` | 0 |
| `test:nc\|D` | 0 |
| `test:nc\|H` | 0 |
| `test:nc\|V` | 0 |
| `test:nc\|X` | 0 |
| `test:nc\|Z` | 0 |
| `test:nc\|mc` | 0 |
| `test:nc\|nc` | 0 |

## <a id="p-.payload.stages.acceptance_construction.outcomes"></a>/payload/stages/acceptance_construction/outcomes

gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:Z\|H, gen:Z\|V, gen:Z\|D, gen:Z\|A, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:X\|H, gen:X\|V, gen:X\|D, gen:X\|A, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:nc\|H, gen:nc\|V, gen:nc\|D, gen:nc\|A, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, gen:mc\|H, gen:mc\|V, gen:mc\|D, gen:mc\|A, test:nc\|Z, test:nc\|X, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|Z, test:H\|X, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|Z, test:V\|X, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|Z, test:D\|X, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|Z, test:A\|X, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|Z, test:mc\|X, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A

## <a id="p-.payload.stages.acceptance_construction.raw_joint_distribution"></a>/payload/stages/acceptance_construction/raw_joint_distribution

| Field | Value |
| --- | --- |
| `x0\|(A,gen)__A` | 7/64 |
| `x0\|(A,gen)__D` | 0 |
| `x0\|(A,gen)__H` | 7/128 |
| `x0\|(A,gen)__V` | 7/128 |
| `x0\|(A,gen)__mc` | 0 |
| `x0\|(A,gen)__nc` | 0 |
| `x0\|(A,test)__A` | 1/64 |
| `x0\|(A,test)__D` | 0 |
| `x0\|(A,test)__H` | 1/128 |
| `x0\|(A,test)__V` | 1/128 |
| `x0\|(A,test)__mc` | 0 |
| `x0\|(A,test)__nc` | 0 |
| `x0\|(D,gen)__A` | 0 |
| `x0\|(D,gen)__D` | 7/64 |
| `x0\|(D,gen)__H` | 7/128 |
| `x0\|(D,gen)__V` | 7/128 |
| `x0\|(D,gen)__mc` | 0 |
| `x0\|(D,gen)__nc` | 0 |
| `x0\|(D,test)__A` | 0 |
| `x0\|(D,test)__D` | 1/64 |
| `x0\|(D,test)__H` | 1/128 |
| `x0\|(D,test)__V` | 1/128 |
| `x0\|(D,test)__mc` | 0 |
| `x0\|(D,test)__nc` | 0 |
| `x0\|(H,gen)__A` | 7/128 |
| `x0\|(H,gen)__D` | 7/128 |
| `x0\|(H,gen)__H` | 7/64 |
| `x0\|(H,gen)__V` | 0 |
| `x0\|(H,gen)__mc` | 0 |
| `x0\|(H,gen)__nc` | 0 |
| `x0\|(H,test)__A` | 1/128 |
| `x0\|(H,test)__D` | 1/128 |
| `x0\|(H,test)__H` | 1/64 |
| `x0\|(H,test)__V` | 0 |
| `x0\|(H,test)__mc` | 0 |
| `x0\|(H,test)__nc` | 0 |
| `x0\|(V,gen)__A` | 7/128 |
| `x0\|(V,gen)__D` | 7/128 |
| `x0\|(V,gen)__H` | 0 |
| `x0\|(V,gen)__V` | 7/64 |
| `x0\|(V,gen)__mc` | 0 |
| `x0\|(V,gen)__nc` | 0 |
| `x0\|(V,test)__A` | 1/128 |
| `x0\|(V,test)__D` | 1/128 |
| `x0\|(V,test)__H` | 0 |
| `x0\|(V,test)__V` | 1/64 |
| `x0\|(V,test)__mc` | 0 |
| `x0\|(V,test)__nc` | 0 |
| `x0\|(mc,gen)__A` | 0 |
| `x0\|(mc,gen)__D` | 0 |
| `x0\|(mc,gen)__H` | 0 |
| `x0\|(mc,gen)__V` | 0 |
| `x0\|(mc,gen)__mc` | 0 |
| `x0\|(mc,gen)__nc` | 0 |
| `x0\|(mc,test)__A` | 0 |
| `x0\|(mc,test)__D` | 0 |
| `x0\|(mc,test)__H` | 0 |
| `x0\|(mc,test)__V` | 0 |
| `x0\|(mc,test)__mc` | 0 |
| `x0\|(mc,test)__nc` | 0 |
| `x0\|(nc,gen)__A` | 0 |
| `x0\|(nc,gen)__D` | 0 |
| `x0\|(nc,gen)__H` | 0 |
| `x0\|(nc,gen)__V` | 0 |
| `x0\|(nc,gen)__mc` | 0 |
| `x0\|(nc,gen)__nc` | 0 |
| `x0\|(nc,test)__A` | 0 |
| `x0\|(nc,test)__D` | 0 |
| `x0\|(nc,test)__H` | 0 |
| `x0\|(nc,test)__V` | 0 |
| `x0\|(nc,test)__mc` | 0 |
| `x0\|(nc,test)__nc` | 0 |

## <a id="p-.payload.stages.compilation"></a>/payload/stages/compilation

| Field | Value |
| --- | --- |
| `refused` | false |

## <a id="p-.payload.stages.key_rate"></a>/payload/stages/key_rate

| Field | Value |
| --- | --- |
| `accumulation_rule` | maximum over the CONTRIBUTING iterates of the first-order linearization O^J_alpha(x_t) + &lt;g_t, v_t - q_t> + b^F_t - &lt;G_t, J_t> of Eq. eq:hlb with the lower bounds of Theorem thm:firstorder (iv): v_t the exact acceptance-side minimiser and b^F_t the feasible-side bound of Lemma lem:feasible-side-dual, verified exactly from the oracle's dual (req:verified-feasible-side) and rounded toward -inf, over every iterate the loop formed at which (H-POS), (H-SUPP) and (H-NOPERT) held and the point was established to lie in AcceptSet x Feas^J(epsilon). Under those hypotheses each bracket is a lower bound on h_low IN EXACT REAL ARITHMETIC (Theorem thm:firstorder (iiib), (iv)), and the maximum of lower bounds is a lower bound. An iterate failing any of them CONTRIBUTES NO BRACKET; the oracle's return and status withdraw none |
| `alpha` | 1.05 |
| `assumption_ids` | A-KEYREG, A-HASH, A-SEED, A-FIXED, A-CONFORM, A-AUTH, A-LAB, A-RHOM, A-SEQ |
| `assumption_ledger` | key_register, pa_hash_family, post_processing_seeds, parameters_fixed_before_run, post_processing_as_analysed, classical_channel_authenticated, laboratory_sealed, laboratory_sealed, round_homogeneity_declaration, sequential_round_model |
| `assurance_reason` | first_order_reported |
| `backend/numpy` | 2.5.3 |
| `backend/oracle/capabilities` | choi_form, complex_hermitian_psd, direct_sum_sectors, equality_rows, inequality_rows |
| `backend/oracle/max_sector_dim` | — |
| `backend/oracle/name` | qics-sector-choi |
| `backend/oracle/version` | 1.1.3 |
| `backend/python` | 3.14.6 |
| `backend/qics` | 1.1.3 |
| `backend/scipy` | 1.18.1 |
| `block_contributions/gen/('A', 'C_1__C_1')` | -0.01083599269652763 |
| `block_contributions/gen/('A', 'C_A__C_1')` | 3.2311742677852644e-27 |
| `block_contributions/gen/('A', 'C_D__C_1')` | 1.6155871338926322e-27 |
| `block_contributions/gen/('A', 'C_H__C_1')` | 1.6155871338926322e-27 |
| `block_contributions/gen/('A', 'C_V__C_1')` | 1.6155871338926322e-27 |
| `block_contributions/gen_X_A` | {} |
| `block_contributions/gen_X_D` | {} |
| `block_contributions/gen_X_H` | {} |
| `block_contributions/gen_X_V` | {} |
| `block_contributions/gen_X_Z` | {} |
| `block_contributions/gen_X_mc` | {} |
| `block_contributions/gen_X_nc` | {} |
| `block_contributions/gen_Z_A` | {} |
| `block_contributions/gen_Z_D` | {} |
| `block_contributions/gen_Z_H` | {} |
| `block_contributions/gen_Z_V` | {} |
| `block_contributions/gen_Z_X` | {} |
| `block_contributions/gen_Z_mc` | {} |
| `block_contributions/gen_Z_nc` | {} |
| `block_contributions/gen_mc_A` | {} |
| `block_contributions/gen_mc_D` | {} |
| `block_contributions/gen_mc_H` | {} |
| `block_contributions/gen_mc_V` | {} |
| `block_contributions/gen_mc_X` | {} |
| `block_contributions/gen_mc_Z` | {} |
| `block_contributions/gen_mc_mc` | {} |
| `block_contributions/gen_mc_nc` | {} |
| `block_contributions/gen_nc_A` | {} |
| `block_contributions/gen_nc_D` | {} |
| `block_contributions/gen_nc_H` | {} |
| `block_contributions/gen_nc_V` | {} |
| `block_contributions/gen_nc_X` | {} |
| `block_contributions/gen_nc_Z` | {} |
| `block_contributions/gen_nc_mc` | {} |
| `block_contributions/gen_nc_nc` | {} |
| `block_contributions/test_A_A` | {} |
| `block_contributions/test_A_D` | {} |
| `block_contributions/test_A_H` | {} |
| `block_contributions/test_A_V` | {} |
| `block_contributions/test_A_X` | {} |
| `block_contributions/test_A_Z` | {} |
| `block_contributions/test_A_mc` | {} |
| `block_contributions/test_A_nc` | {} |
| `block_contributions/test_D_A` | {} |
| `block_contributions/test_D_D` | {} |
| `block_contributions/test_D_H` | {} |
| `block_contributions/test_D_V` | {} |
| `block_contributions/test_D_X` | {} |
| `block_contributions/test_D_Z` | {} |
| `block_contributions/test_D_mc` | {} |
| `block_contributions/test_D_nc` | {} |
| `block_contributions/test_H_A` | {} |
| `block_contributions/test_H_D` | {} |
| `block_contributions/test_H_H` | {} |
| `block_contributions/test_H_V` | {} |
| `block_contributions/test_H_X` | {} |
| `block_contributions/test_H_Z` | {} |
| `block_contributions/test_H_mc` | {} |
| `block_contributions/test_H_nc` | {} |
| `block_contributions/test_V_A` | {} |
| `block_contributions/test_V_D` | {} |
| `block_contributions/test_V_H` | {} |
| `block_contributions/test_V_V` | {} |
| `block_contributions/test_V_X` | {} |
| `block_contributions/test_V_Z` | {} |
| `block_contributions/test_V_mc` | {} |
| `block_contributions/test_V_nc` | {} |
| `block_contributions/test_mc_A` | {} |
| `block_contributions/test_mc_D` | {} |
| `block_contributions/test_mc_H` | {} |
| `block_contributions/test_mc_V` | {} |
| `block_contributions/test_mc_X` | {} |
| `block_contributions/test_mc_Z` | {} |
| `block_contributions/test_mc_mc` | {} |
| `block_contributions/test_mc_nc` | {} |
| `block_contributions/test_nc_A` | {} |
| `block_contributions/test_nc_D` | {} |
| `block_contributions/test_nc_H` | {} |
| `block_contributions/test_nc_V` | {} |
| `block_contributions/test_nc_X` | {} |
| `block_contributions/test_nc_Z` | {} |
| `block_contributions/test_nc_mc` | {} |
| `block_contributions/test_nc_nc` | {} |
| `certified/arithmetic_library` | python-flint 0.9.0 |
| `certified/certified_bound` | 0.40193730397769356 |
| `certified/certified_evaluation` | on |
| `certified/certified_minus_first_order` | 3.997068352654831e-14 |
| `certified/declaration` | reference_companion |
| `certified/first_order_key_length` | 40193071 |
| `certified/max_gradient_radius` | 4.4784641503450993e-32 |
| `certified/points/0/acceptance_side_bound` | 30.698533593845404 |
| `certified/points/0/certified` | true |
| `certified/points/0/certified_bracket` | 0.40193730397769356 |
| `certified/points/0/detail` | \[\] |
| `certified/points/0/feasible_side_bound` | -30.296596289867715 |
| `certified/points/0/gradient_radius` | 4.4784641503450993e-32 |
| `certified/points/0/index` | 0 |
| `certified/points/0/iteration` | 3 |
| `certified/points/0/reasons` | \[\] |
| `certified/points/0/sequence` | 13 |
| `certified/points/0/set` | polish |
| `certified/points/1/acceptance_side_bound` | 30.698533593855412 |
| `certified/points/1/certified` | true |
| `certified/points/1/certified_bracket` | 0.4019272453245413 |
| `certified/points/1/detail` | \[\] |
| `certified/points/1/feasible_side_bound` | -30.296606348530872 |
| `certified/points/1/gradient_radius` | 1.303702897763059e-32 |
| `certified/points/1/index` | 1 |
| `certified/points/1/iteration` | 2 |
| `certified/points/1/reasons` | \[\] |
| `certified/points/1/sequence` | 12 |
| `certified/points/1/set` | polish |
| `certified/points/2/acceptance_side_bound` | 30.698534513096657 |
| `certified/points/2/certified` | true |
| `certified/points/2/certified_bracket` | 0.4017486577000903 |
| `certified/points/2/detail` | \[\] |
| `certified/points/2/feasible_side_bound` | -30.29678585539657 |
| `certified/points/2/gradient_radius` | 6.9543825795659335e-34 |
| `certified/points/2/index` | 2 |
| `certified/points/2/iteration` | 10 |
| `certified/points/2/reasons` | \[\] |
| `certified/points/2/sequence` | 10 |
| `certified/points/2/set` | search |
| `certified/points/3/acceptance_side_bound` | 30.698534513640446 |
| `certified/points/3/certified` | true |
| `certified/points/3/certified_bracket` | 0.40133617804836125 |
| `certified/points/3/detail` | \[\] |
| `certified/points/3/feasible_side_bound` | -30.297198335592086 |
| `certified/points/3/gradient_radius` | 7.1827818924434065e-34 |
| `certified/points/3/index` | 3 |
| `certified/points/3/iteration` | 9 |
| `certified/points/3/reasons` | \[\] |
| `certified/points/3/sequence` | 9 |
| `certified/points/3/set` | search |
| `certified/points/4/acceptance_side_bound` | 30.698534550707425 |
| `certified/points/4/certified` | true |
| `certified/points/4/certified_bracket` | 0.4011111887161994 |
| `certified/points/4/detail` | \[\] |
| `certified/points/4/feasible_side_bound` | -30.297423361991232 |
| `certified/points/4/gradient_radius` | 7.234600645122404e-34 |
| `certified/points/4/index` | 4 |
| `certified/points/4/iteration` | 8 |
| `certified/points/4/reasons` | \[\] |
| `certified/points/4/sequence` | 8 |
| `certified/points/4/set` | search |
| `certified/premises` | \[\] |
| `certified/reasons` | \[\] |
| `certified/resting_blocks` | \[\] |
| `certified/seconds` | 0.09219220001250505 |
| `certified/status` | certified |
| `certified/working_precision_bits` | 128 |
| `claim_roots` | meat-core/frank-wolfe/cor:fo-reference, meat-core/frank-wolfe/cor:certified-keylength, meat-core/frank-wolfe/cor:certified-keylength-reference, meat-core/cor:keylength-bound |
| `constraint_entries_through_a_reductions_chain` | 0 |
| `deductions/accepted_state_flag_bonus` | 1.0 |
| `deductions/error_correction_lambda_ec` | 0.0 |
| `deductions/error_verification` | 30.0 |
| `deductions/privacy_amplification` | 629.9999999999994 |
| `deductions/two_universal_hash_penalty` | 0.0 |
| `dropped_set` | \[\] |
| `estimate_point_relaxed_member` | true |
| `first_order_clamped` | false |
| `first_order_minus_estimate` | -8.787649046215762e-07 |
| `frank_wolfe_gap` | 0.00019000032208549202 |
| `group_b_worst/constraint_rows/consumed_point/at` | — |
| `group_b_worst/constraint_rows/consumed_point/iteration` | 1 |
| `group_b_worst/constraint_rows/consumed_point/worst` | 0.0 |
| `group_b_worst/constraint_rows/declared` | 1e-07 |
| `group_b_worst/constraint_rows/kind` | spectral_floor |
| `group_b_worst/constraint_rows/returned_point/at` | — |
| `group_b_worst/constraint_rows/returned_point/iteration` | — |
| `group_b_worst/constraint_rows/returned_point/worst` | 0.0 |
| `group_b_worst/iterate_coupling/consumed_point/at` | \* |
| `group_b_worst/iterate_coupling/consumed_point/iteration` | 2 |
| `group_b_worst/iterate_coupling/consumed_point/worst` | 2.8261415430108627e-10 |
| `group_b_worst/iterate_coupling/declared` | 1e-07 |
| `group_b_worst/iterate_coupling/kind` | entrywise |
| `group_b_worst/iterate_coupling/returned_point/at` | \* |
| `group_b_worst/iterate_coupling/returned_point/iteration` | — |
| `group_b_worst/iterate_coupling/returned_point/worst` | 2.6718871559694435e-10 |
| `group_b_worst/iterate_positivity/at` | A\_\_C_0\_\_C_1 |
| `group_b_worst/iterate_positivity/declared` | 0.0 |
| `group_b_worst/iterate_positivity/iteration` | 10 |
| `group_b_worst/iterate_positivity/kind` | spectral_floor |
| `group_b_worst/iterate_positivity/returned_point/at` | A\_\_C_0\_\_C_1 |
| `group_b_worst/iterate_positivity/returned_point/iteration` | — |
| `group_b_worst/iterate_positivity/returned_point/worst` | 7.103615361783254e-13 |
| `group_b_worst/iterate_positivity/worst` | 7.139033309853558e-13 |
| `group_b_worst/iterate_repair_window/at` | — |
| `group_b_worst/iterate_repair_window/declared` | 1e-07 |
| `group_b_worst/iterate_repair_window/iteration` | — |
| `group_b_worst/iterate_repair_window/kind` | spectral_floor |
| `group_b_worst/iterate_repair_window/note` | this driver takes the REJECT branch of rem:fo-iterate-repair and repairs no formed iterate, so nothing was compared against the window as a repair |
| `group_b_worst/iterate_repair_window/worst` | — |
| `group_b_worst/optimizer_gap/at` | — |
| `group_b_worst/optimizer_gap/declared` | 1e-10 |
| `group_b_worst/optimizer_gap/iteration` | 10 |
| `group_b_worst/optimizer_gap/kind` | not_a_predicate |
| `group_b_worst/optimizer_gap/worst` | 0.00019000032208549202 |
| `group_b_worst/oracle_repair_window/at/block` | A\_\_C_mc\_\_C_A |
| `group_b_worst/oracle_repair_window/at/group` | \* |
| `group_b_worst/oracle_repair_window/declared` | 1e-07 |
| `group_b_worst/oracle_repair_window/iteration` | 10 |
| `group_b_worst/oracle_repair_window/kind` | spectral_floor |
| `group_b_worst/oracle_repair_window/repairs` | 391 |
| `group_b_worst/oracle_repair_window/worst` | -1.3470595893907474e-11 |
| `h_lb` | 0.4019373039776536 |
| `h_low` | 0.4019381827425582 |
| `h_low_is_infinite` | false |
| `iterations` | 10 |
| `joint_solver/oracle` | qics |
| `joint_solver/oracle_assignment/*` | qics |
| `joint_solver/oracle_calls/qics` | 10 |
| `joint_solver/pairwise` | — |
| `joint_solver/q_rule` | box-partial-minimum |
| `joint_solver/spectral_evidence` | — |
| `joint_solver/step_rule` | vanilla |
| `joint_solver/warm_start` | — |
| `key_length` | 40193071 |
| `key_length_reason` | certified_reported: the bracket was formed again at the run's final points from the declaration's data with every arithmetic step exact or rigorously enclosed (frank-wolfe/req:certified-evaluation), and the key length is computed exactly from max{0, h_cert} by frank-wolfe/cor:certified-keylength; the first-order number and its key length are recorded beside it |
| `key_length_reason_code` | certified_reported |
| `map_validation_report/alice_sectors` | A |
| `map_validation_report/declaration_admitted_exactly` | true |
| `map_validation_report/factor_labels` | alice_station, bob_station |
| `map_validation_report/hsupp_reference_band/factor_support_cutoff` | 1e-06 |
| `map_validation_report/hsupp_reference_band/note` | per key-active pair, the directions of ran K whose singular value lies in (support_cutoff, sqrt(support_cutoff)\] relative to the largest: not counted in dim W under rem:fo-one-ruler, and no rank of X counts them either. Diagnostic only; decides nothing |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_A__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_D__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_H__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_V__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/relative_to` | the largest singular value of the pair's Kraus stack |
| `map_validation_report/hsupp_reference_band/support_cutoff` | 1e-12 |
| `mathematical_spec_version` | meat-core@1.28.0 |
| `module_versions/meat-core` | 1.32.0 |
| `module_versions/meat-core/frank-wolfe` | 0.19.0 |
| `net_key_length` | 40193071 |
| `optimized_q/gen` | 0.43719511 |
| `optimized_q/gen_X_A` | 0.0 |
| `optimized_q/gen_X_D` | 0.0 |
| `optimized_q/gen_X_H` | 0.0 |
| `optimized_q/gen_X_V` | 0.0 |
| `optimized_q/gen_X_Z` | 0.21900409 |
| `optimized_q/gen_X_mc` | 0.0 |
| `optimized_q/gen_X_nc` | 0.0 |
| `optimized_q/gen_Z_A` | 0.0 |
| `optimized_q/gen_Z_D` | 0.0 |
| `optimized_q/gen_Z_H` | 0.0 |
| `optimized_q/gen_Z_V` | 0.0 |
| `optimized_q/gen_Z_X` | 0.21900409 |
| `optimized_q/gen_Z_mc` | 0.0 |
| `optimized_q/gen_Z_nc` | 0.0 |
| `optimized_q/gen_mc_A` | 0.0 |
| `optimized_q/gen_mc_D` | 0.0 |
| `optimized_q/gen_mc_H` | 0.0 |
| `optimized_q/gen_mc_V` | 0.0 |
| `optimized_q/gen_mc_X` | 0.0 |
| `optimized_q/gen_mc_Z` | 0.0 |
| `optimized_q/gen_mc_mc` | 0.0 |
| `optimized_q/gen_mc_nc` | 0.0 |
| `optimized_q/gen_nc_A` | 0.0 |
| `optimized_q/gen_nc_D` | 0.0 |
| `optimized_q/gen_nc_H` | 0.0 |
| `optimized_q/gen_nc_V` | 0.0 |
| `optimized_q/gen_nc_X` | 0.0 |
| `optimized_q/gen_nc_Z` | 0.0 |
| `optimized_q/gen_nc_mc` | 0.0 |
| `optimized_q/gen_nc_nc` | 0.0 |
| `optimized_q/test_A_A` | 0.015548729999999998 |
| `optimized_q/test_A_D` | 0.0 |
| `optimized_q/test_A_H` | 0.007824511989629435 |
| `optimized_q/test_A_V` | 0.007825935611953857 |
| `optimized_q/test_A_X` | 0.0 |
| `optimized_q/test_A_Z` | 0.0 |
| `optimized_q/test_A_mc` | 0.0 |
| `optimized_q/test_A_nc` | 0.0 |
| `optimized_q/test_D_A` | 0.0 |
| `optimized_q/test_D_D` | 0.015548729999999998 |
| `optimized_q/test_D_H` | 0.007825935551072591 |
| `optimized_q/test_D_V` | 0.007824511847344114 |
| `optimized_q/test_D_X` | 0.0 |
| `optimized_q/test_D_Z` | 0.0 |
| `optimized_q/test_D_mc` | 0.0 |
| `optimized_q/test_D_nc` | 0.0 |
| `optimized_q/test_H_A` | 0.007824716354145148 |
| `optimized_q/test_H_D` | 0.0078257312820705 |
| `optimized_q/test_H_H` | 0.015548729999999998 |
| `optimized_q/test_H_V` | 0.0 |
| `optimized_q/test_H_X` | 0.0 |
| `optimized_q/test_H_Z` | 0.0 |
| `optimized_q/test_H_mc` | 0.0 |
| `optimized_q/test_H_nc` | 0.0 |
| `optimized_q/test_V_A` | 0.007825731245101879 |
| `optimized_q/test_V_D` | 0.007824716118682466 |
| `optimized_q/test_V_H` | 0.0 |
| `optimized_q/test_V_V` | 0.015548729999999998 |
| `optimized_q/test_V_X` | 0.0 |
| `optimized_q/test_V_Z` | 0.0 |
| `optimized_q/test_V_mc` | 0.0 |
| `optimized_q/test_V_nc` | 0.0 |
| `optimized_q/test_mc_A` | 0.0 |
| `optimized_q/test_mc_D` | 0.0 |
| `optimized_q/test_mc_H` | 0.0 |
| `optimized_q/test_mc_V` | 0.0 |
| `optimized_q/test_mc_X` | 0.0 |
| `optimized_q/test_mc_Z` | 0.0 |
| `optimized_q/test_mc_mc` | 0.0 |
| `optimized_q/test_mc_nc` | 0.0 |
| `optimized_q/test_nc_A` | 0.0 |
| `optimized_q/test_nc_D` | 0.0 |
| `optimized_q/test_nc_H` | 0.0 |
| `optimized_q/test_nc_V` | 0.0 |
| `optimized_q/test_nc_X` | 0.0 |
| `optimized_q/test_nc_Z` | 0.0 |
| `optimized_q/test_nc_mc` | 0.0 |
| `optimized_q/test_nc_nc` | 0.0 |
| `optimizer_certificate` | an object of 16 fields (132,494 characters); not shown, see the record |
| `oracle_diagnostics` | a list of 10 items (109,081 characters); not shown, see the record |
| `per_iterate` | a list of 10 items (6,017 characters); not shown, see the record |
| `predicted_statistics/gen` | 0.43750000001621037 |
| `predicted_statistics/gen_X_A` | 0.0 |
| `predicted_statistics/gen_X_D` | 0.0 |
| `predicted_statistics/gen_X_H` | 0.0 |
| `predicted_statistics/gen_X_V` | 0.0 |
| `predicted_statistics/gen_X_Z` | 0.21875000000808648 |
| `predicted_statistics/gen_X_mc` | 3.839017474294645e-11 |
| `predicted_statistics/gen_X_nc` | 2.797048548707244e-12 |
| `predicted_statistics/gen_Z_A` | 0.0 |
| `predicted_statistics/gen_Z_D` | 0.0 |
| `predicted_statistics/gen_Z_H` | 0.0 |
| `predicted_statistics/gen_Z_V` | 0.0 |
| `predicted_statistics/gen_Z_X` | 0.21875000000808648 |
| `predicted_statistics/gen_Z_mc` | 3.8390137334006094e-11 |
| `predicted_statistics/gen_Z_nc` | 2.797048548707244e-12 |
| `predicted_statistics/gen_mc_A` | 0.0 |
| `predicted_statistics/gen_mc_D` | 0.0 |
| `predicted_statistics/gen_mc_H` | 0.0 |
| `predicted_statistics/gen_mc_V` | 0.0 |
| `predicted_statistics/gen_mc_X` | 3.8390174743184596e-11 |
| `predicted_statistics/gen_mc_Z` | 3.839013733369848e-11 |
| `predicted_statistics/gen_mc_mc` | 2.0808023874242898e-11 |
| `predicted_statistics/gen_mc_nc` | 6.5264466136338425e-12 |
| `predicted_statistics/gen_nc_A` | 0.0 |
| `predicted_statistics/gen_nc_D` | 0.0 |
| `predicted_statistics/gen_nc_H` | 0.0 |
| `predicted_statistics/gen_nc_V` | 0.0 |
| `predicted_statistics/gen_nc_X` | 2.797048548707244e-12 |
| `predicted_statistics/gen_nc_Z` | 2.797048548707244e-12 |
| `predicted_statistics/gen_nc_mc` | 6.5264466136338425e-12 |
| `predicted_statistics/gen_nc_nc` | 2.797048548705548e-12 |
| `predicted_statistics/test_A_A` | 0.014928286736163148 |
| `predicted_statistics/test_A_D` | 0.0006967133658339157 |
| `predicted_statistics/test_A_H` | 0.007811789397234772 |
| `predicted_statistics/test_A_V` | 0.007813210704760954 |
| `predicted_statistics/test_A_X` | 0.0 |
| `predicted_statistics/test_A_Z` | 0.0 |
| `predicted_statistics/test_A_mc` | 2.74215533878189e-12 |
| `predicted_statistics/test_A_nc` | 1.9978918205051745e-13 |
| `predicted_statistics/test_D_A` | 0.0006967133635014517 |
| `predicted_statistics/test_D_D` | 0.014928286535659373 |
| `predicted_statistics/test_D_H` | 0.007813210643978682 |
| `predicted_statistics/test_D_V` | 0.007811789255180805 |
| `predicted_statistics/test_D_X` | 0.0 |
| `predicted_statistics/test_D_Z` | 0.0 |
| `predicted_statistics/test_D_mc` | 2.7421553387818866e-12 |
| `predicted_statistics/test_D_nc` | 1.9978918205051745e-13 |
| `predicted_statistics/test_H_A` | 0.007811993429455456 |
| `predicted_statistics/test_H_D` | 0.007813006707116318 |
| `predicted_statistics/test_H_H` | 0.014935055631371494 |
| `predicted_statistics/test_H_V` | 0.0006899445052016065 |
| `predicted_statistics/test_H_X` | 0.0 |
| `predicted_statistics/test_H_Z` | 0.0 |
| `predicted_statistics/test_H_mc` | 2.742152666715521e-12 |
| `predicted_statistics/test_H_nc` | 1.9978918205051745e-13 |
| `predicted_statistics/test_V_A` | 0.007813006670207805 |
| `predicted_statistics/test_V_D` | 0.007811993194375634 |
| `predicted_statistics/test_V_H` | 0.0006899444098432873 |
| `predicted_statistics/test_V_V` | 0.01493505545474148 |
| `predicted_statistics/test_V_X` | 0.0 |
| `predicted_statistics/test_V_Z` | 0.0 |
| `predicted_statistics/test_V_mc` | 2.7421526667139197e-12 |
| `predicted_statistics/test_V_nc` | 1.9978918205051745e-13 |
| `predicted_statistics/test_mc_A` | 2.7421553387986815e-12 |
| `predicted_statistics/test_mc_D` | 2.742155338799117e-12 |
| `predicted_statistics/test_mc_H` | 2.742152666693586e-12 |
| `predicted_statistics/test_mc_V` | 2.7421526666919105e-12 |
| `predicted_statistics/test_mc_X` | 0.0 |
| `predicted_statistics/test_mc_Z` | 0.0 |

124 more fields are not shown; see the record.

## <a id="p-.payload.stages.key_rate.alpha"></a>/payload/stages/key_rate/alpha

`1.05`

## <a id="p-.payload.stages.key_rate.certified.certified_bound"></a>/payload/stages/key_rate/certified/certified_bound

`0.40193730397769356`

## <a id="p-.payload.stages.key_rate.deductions"></a>/payload/stages/key_rate/deductions

| Field | Value |
| --- | --- |
| `accepted_state_flag_bonus` | 1.0 |
| `error_correction_lambda_ec` | 0.0 |
| `error_verification` | 30.0 |
| `privacy_amplification` | 629.9999999999994 |
| `two_universal_hash_penalty` | 0.0 |

## <a id="p-.payload.stages.key_rate.deductions.error_verification"></a>/payload/stages/key_rate/deductions/error_verification

`30.0`

## <a id="p-.payload.stages.key_rate.deductions.two_universal_hash_penalty"></a>/payload/stages/key_rate/deductions/two_universal_hash_penalty

`0.0`

## <a id="p-.payload.stages.key_rate.estimate_point_relaxed_member"></a>/payload/stages/key_rate/estimate_point_relaxed_member

`true`

## <a id="p-.payload.stages.key_rate.first_order_clamped"></a>/payload/stages/key_rate/first_order_clamped

`false`

## <a id="p-.payload.stages.key_rate.first_order_minus_estimate"></a>/payload/stages/key_rate/first_order_minus_estimate

`-8.787649046215762e-07`

## <a id="p-.payload.stages.key_rate.frank_wolfe_gap"></a>/payload/stages/key_rate/frank_wolfe_gap

`0.00019000032208549202`

## <a id="p-.payload.stages.key_rate.group_b_worst"></a>/payload/stages/key_rate/group_b_worst

| Field | Value |
| --- | --- |
| `constraint_rows/consumed_point/at` | — |
| `constraint_rows/consumed_point/iteration` | 1 |
| `constraint_rows/consumed_point/worst` | 0.0 |
| `constraint_rows/declared` | 1e-07 |
| `constraint_rows/kind` | spectral_floor |
| `constraint_rows/returned_point/at` | — |
| `constraint_rows/returned_point/iteration` | — |
| `constraint_rows/returned_point/worst` | 0.0 |
| `iterate_coupling/consumed_point/at` | \* |
| `iterate_coupling/consumed_point/iteration` | 2 |
| `iterate_coupling/consumed_point/worst` | 2.8261415430108627e-10 |
| `iterate_coupling/declared` | 1e-07 |
| `iterate_coupling/kind` | entrywise |
| `iterate_coupling/returned_point/at` | \* |
| `iterate_coupling/returned_point/iteration` | — |
| `iterate_coupling/returned_point/worst` | 2.6718871559694435e-10 |
| `iterate_positivity/at` | A\_\_C_0\_\_C_1 |
| `iterate_positivity/declared` | 0.0 |
| `iterate_positivity/iteration` | 10 |
| `iterate_positivity/kind` | spectral_floor |
| `iterate_positivity/returned_point/at` | A\_\_C_0\_\_C_1 |
| `iterate_positivity/returned_point/iteration` | — |
| `iterate_positivity/returned_point/worst` | 7.103615361783254e-13 |
| `iterate_positivity/worst` | 7.139033309853558e-13 |
| `iterate_repair_window/at` | — |
| `iterate_repair_window/declared` | 1e-07 |
| `iterate_repair_window/iteration` | — |
| `iterate_repair_window/kind` | spectral_floor |
| `iterate_repair_window/note` | this driver takes the REJECT branch of rem:fo-iterate-repair and repairs no formed iterate, so nothing was compared against the window as a repair |
| `iterate_repair_window/worst` | — |
| `optimizer_gap/at` | — |
| `optimizer_gap/declared` | 1e-10 |
| `optimizer_gap/iteration` | 10 |
| `optimizer_gap/kind` | not_a_predicate |
| `optimizer_gap/worst` | 0.00019000032208549202 |
| `oracle_repair_window/at/block` | A\_\_C_mc\_\_C_A |
| `oracle_repair_window/at/group` | \* |
| `oracle_repair_window/declared` | 1e-07 |
| `oracle_repair_window/iteration` | 10 |
| `oracle_repair_window/kind` | spectral_floor |
| `oracle_repair_window/repairs` | 391 |
| `oracle_repair_window/worst` | -1.3470595893907474e-11 |

## <a id="p-.payload.stages.key_rate.h_lb"></a>/payload/stages/key_rate/h_lb

`0.4019373039776536`

## <a id="p-.payload.stages.key_rate.h_low"></a>/payload/stages/key_rate/h_low

`0.4019381827425582`

## <a id="p-.payload.stages.key_rate.iterations"></a>/payload/stages/key_rate/iterations

`10`

## <a id="p-.payload.stages.key_rate.joint_solver"></a>/payload/stages/key_rate/joint_solver

| Field | Value |
| --- | --- |
| `oracle` | qics |
| `oracle_assignment/*` | qics |
| `oracle_calls/qics` | 10 |
| `pairwise` | — |
| `q_rule` | box-partial-minimum |
| `spectral_evidence` | — |
| `step_rule` | vanilla |
| `warm_start` | — |

## <a id="p-.payload.stages.key_rate.key_length"></a>/payload/stages/key_rate/key_length

`40193071`

## <a id="p-.payload.stages.key_rate.per_iterate"></a>/payload/stages/key_rate/per_iterate

| Field | Value |
| --- | --- |
| `0/acceptance_iterate_exact` | true |
| `0/constraint_row_residual` | 0.0 |
| `0/coupling_residual` | 0.0 |
| `0/coupling_residual_at` | \* |
| `0/dual_gap` | -2.0886879781301104e-08 |
| `0/feasible_side_bound` | -228.84188596830123 |
| `0/feasible_side_multipliers/*` | zero |
| `0/frame_deduction` | 0.0 |
| `0/iteration` | 1 |
| `0/linearization` | -137.80759772090374 |
| `0/min_block_eigenvalue` | 0.00390625 |
| `0/min_block_eigenvalue_at` | A\_\_C_1\_\_C_1 |
| `0/objective` | 60.73769238872926 |
| `0/oracle_optimal` | true |
| `0/oracle_pairing` | -228.84188598918809 |
| `0/oracle_status` | optimal |
| `0/row_multiplier_norm` | 0.0 |
| `0/withdrawal` | — |
| `1/acceptance_iterate_exact` | true |
| `1/constraint_row_residual` | 0.0 |
| `1/coupling_residual` | 2.8261415430108627e-10 |
| `1/coupling_residual_at` | \* |
| `1/dual_gap` | -3.2448836319658413e-12 |
| `1/feasible_side_bound` | -43.422472064174656 |
| `1/feasible_side_multipliers/*` | zero |
| `1/frame_deduction` | 0.0 |
| `1/iteration` | 2 |
| `1/linearization` | -12.688675374918551 |
| `1/min_block_eigenvalue` | 7.821122222084753e-13 |
| `1/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `1/objective` | 0.4372008305879074 |
| `1/oracle_optimal` | true |
| `1/oracle_pairing` | -43.422472064177896 |
| `1/oracle_status` | optimal |
| `1/row_multiplier_norm` | 0.0 |
| `1/withdrawal` | — |
| `2/acceptance_iterate_exact` | true |
| `2/constraint_row_residual` | 0.0 |
| `2/coupling_residual` | 2.7781155154116277e-10 |
| `2/coupling_residual_at` | \* |
| `2/dual_gap` | -1.9439419962475692e-09 |
| `2/feasible_side_bound` | -44.044599061825316 |
| `2/feasible_side_multipliers/*` | zero |
| `2/frame_deduction` | 0.0 |
| `2/iteration` | 3 |
| `2/linearization` | -13.328300619127942 |
| `2/min_block_eigenvalue` | 7.474673111607339e-13 |
| `2/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `2/objective` | 0.41970258402916333 |
| `2/oracle_optimal` | true |
| `2/oracle_pairing` | -44.044599063769255 |
| `2/oracle_status` | optimal |
| `2/row_multiplier_norm` | 0.0 |
| `2/withdrawal` | — |
| `3/acceptance_iterate_exact` | true |
| `3/constraint_row_residual` | 0.0 |
| `3/coupling_residual` | 2.777764684935846e-10 |
| `3/coupling_residual_at` | \* |
| `3/dual_gap` | -1.004282066860757e-10 |
| `3/feasible_side_bound` | -34.127176735911036 |
| `3/feasible_side_multipliers/*` | zero |
| `3/frame_deduction` | 0.0 |
| `3/iteration` | 4 |
| `3/linearization` | -3.4110413864148685 |
| `3/min_block_eigenvalue` | 7.472701094954897e-13 |
| `3/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `3/objective` | 0.41953949082796405 |
| `3/oracle_optimal` | true |
| `3/oracle_pairing` | -34.127176736011464 |
| `3/oracle_status` | optimal |
| `3/row_multiplier_norm` | 0.0 |
| `3/withdrawal` | — |
| `4/acceptance_iterate_exact` | true |
| `4/constraint_row_residual` | 0.0 |
| `4/coupling_residual` | 2.666791232286414e-10 |
| `4/coupling_residual_at` | \* |
| `4/dual_gap` | -9.030602482120162e-11 |
| `4/feasible_side_bound` | -31.74514359085847 |
| `4/feasible_side_multipliers/*` | zero |
| `4/frame_deduction` | 0.0 |
| `4/iteration` | 5 |
| `4/linearization` | -1.0457816622151739 |
| `4/min_block_eigenvalue` | 7.165198084942153e-13 |
| `4/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `4/objective` | 0.4027660699750959 |
| `4/oracle_optimal` | true |
| `4/oracle_pairing` | -31.74514359094877 |
| `4/oracle_status` | optimal |
| `4/row_multiplier_norm` | 0.0 |
| `4/withdrawal` | — |
| `5/acceptance_iterate_exact` | true |
| `5/constraint_row_residual` | 0.0 |
| `5/coupling_residual` | 2.662499110073213e-10 |
| `5/coupling_residual_at` | \* |
| `5/dual_gap` | -3.0247353411460683e-10 |
| `5/feasible_side_bound` | -30.316099004260877 |
| `5/feasible_side_multipliers/*` | zero |
| `5/frame_deduction` | 0.0 |
| `5/iteration` | 6 |
| `5/linearization` | 0.38245355117247987 |
| `5/min_block_eigenvalue` | 7.153089969707001e-13 |
| `5/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `5/objective` | 0.4019566967651854 |
| `5/oracle_optimal` | true |
| `5/oracle_pairing` | -30.31609900456335 |
| `5/oracle_status` | optimal |
| `5/row_multiplier_norm` | 0.0 |
| `5/withdrawal` | — |
| `6/acceptance_iterate_exact` | true |
| `6/constraint_row_residual` | 0.0 |
| `6/coupling_residual` | 2.6585644796739416e-10 |
| `6/coupling_residual_at` | \* |
| `6/dual_gap` | -2.2743253888913984e-10 |
| `6/feasible_side_bound` | -30.309085822807067 |
| `6/feasible_side_multipliers/*` | zero |
| `6/frame_deduction` | 0.0 |
| `6/iteration` | 7 |
| `6/linearization` | 0.38944895839166466 |
| `6/min_block_eigenvalue` | 7.139950424968134e-13 |
| `6/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `6/objective` | 0.4019389225305249 |
| `6/oracle_optimal` | true |
| `6/oracle_pairing` | -30.309085823034497 |
| `6/oracle_status` | optimal |
| `6/row_multiplier_norm` | 0.0 |
| `6/withdrawal` | — |
| `7/acceptance_iterate_exact` | true |
| `7/constraint_row_residual` | 0.0 |
| `7/coupling_residual` | 2.6584845436161686e-10 |
| `7/coupling_residual_at` | \* |
| `7/dual_gap` | -3.4290740351900016e-11 |
| `7/feasible_side_bound` | -30.29742336199121 |
| `7/feasible_side_multipliers/*` | zero |
| `7/frame_deduction` | 0.0 |
| `7/iteration` | 8 |
| `7/linearization` | 0.4011111887161824 |
| `7/min_block_eigenvalue` | 7.139686048276508e-13 |
| `7/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `7/objective` | 0.4019386920392066 |
| `7/oracle_optimal` | true |
| `7/oracle_pairing` | -30.297423362025498 |
| `7/oracle_status` | optimal |
| `7/row_multiplier_norm` | 0.0 |
| `7/withdrawal` | — |
| `8/acceptance_iterate_exact` | true |
| `8/constraint_row_residual` | 0.0 |
| `8/coupling_residual` | 2.658266939903342e-10 |
| `8/coupling_residual_at` | \* |
| `8/dual_gap` | -6.885397024040452e-12 |
| `8/feasible_side_bound` | -30.29719833559207 |
| `8/feasible_side_multipliers/*` | zero |
| `8/frame_deduction` | 0.0 |
| `8/iteration` | 9 |
| `8/linearization` | 0.4013361780483779 |
| `8/min_block_eigenvalue` | 7.139046194149968e-13 |
| `8/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `8/objective` | 0.4019386549722289 |
| `8/oracle_optimal` | true |
| `8/oracle_pairing` | -30.297198335598956 |
| `8/oracle_status` | optimal |
| `8/row_multiplier_norm` | 0.0 |
| `8/withdrawal` | — |
| `9/acceptance_iterate_exact` | true |
| `9/constraint_row_residual` | 0.0 |
| `9/coupling_residual` | 2.6582602785651943e-10 |
| `9/coupling_residual_at` | \* |
| `9/dual_gap` | -3.5937268493631483e-09 |
| `9/feasible_side_bound` | -30.296785855396557 |
| `9/feasible_side_multipliers/*` | zero |
| `9/frame_deduction` | 0.0 |
| `9/iteration` | 10 |
| `9/linearization` | 0.4017486577000748 |
| `9/min_block_eigenvalue` | 7.139033309853558e-13 |
| `9/min_block_eigenvalue_at` | A\_\_C_0\_\_C_1 |
| `9/objective` | 0.4019386544284414 |
| `9/oracle_optimal` | true |
| `9/oracle_pairing` | -30.296785858990283 |
| `9/oracle_status` | optimal |
| `9/row_multiplier_norm` | 0.0 |
| `9/withdrawal` | — |

## <a id="p-.payload.stages.key_rate.search_report"></a>/payload/stages/key_rate/search_report

| Field | Value |
| --- | --- |
| `assessment_history/0/contributes` | true |
| `assessment_history/0/elapsed_seconds` | 0.08634939999319613 |
| `assessment_history/0/objective` | 60.73769238872926 |
| `assessment_history/0/raw_bracket` | -137.80759772090374 |
| `assessment_history/0/raw_gap` | 198.54529013051987 |
| `assessment_history/0/withdrawal` | — |
| `assessment_history/1/contributes` | true |
| `assessment_history/1/elapsed_seconds` | 0.19169610005337745 |
| `assessment_history/1/objective` | 0.4372008305879074 |
| `assessment_history/1/raw_bracket` | -12.688675374918551 |
| `assessment_history/1/raw_gap` | 13.125876205509655 |
| `assessment_history/1/withdrawal` | — |
| `assessment_history/2/contributes` | true |
| `assessment_history/2/elapsed_seconds` | 0.2953964000334963 |
| `assessment_history/2/objective` | 0.41970258402916333 |
| `assessment_history/2/raw_bracket` | -13.328300619127942 |
| `assessment_history/2/raw_gap` | 13.748003205101034 |
| `assessment_history/2/withdrawal` | — |
| `assessment_history/3/contributes` | true |
| `assessment_history/3/elapsed_seconds` | 0.4051168999867514 |
| `assessment_history/3/objective` | 0.41953949082796405 |
| `assessment_history/3/raw_bracket` | -3.4110413864148685 |
| `assessment_history/3/raw_gap` | 3.830580877343243 |
| `assessment_history/3/withdrawal` | — |
| `assessment_history/4/contributes` | true |
| `assessment_history/4/elapsed_seconds` | 0.5157415999565274 |
| `assessment_history/4/objective` | 0.4027660699750959 |
| `assessment_history/4/raw_bracket` | -1.0457816622151739 |
| `assessment_history/4/raw_gap` | 1.4485477322805633 |
| `assessment_history/4/withdrawal` | — |
| `assessment_history/5/contributes` | true |
| `assessment_history/5/elapsed_seconds` | 0.6272470999974757 |
| `assessment_history/5/objective` | 0.4019566967651854 |
| `assessment_history/5/raw_bracket` | 0.38245355117247987 |
| `assessment_history/5/raw_gap` | 0.019503145895189478 |
| `assessment_history/5/withdrawal` | — |
| `assessment_history/6/contributes` | true |
| `assessment_history/6/elapsed_seconds` | 0.7348964000120759 |
| `assessment_history/6/objective` | 0.4019389225305249 |
| `assessment_history/6/raw_bracket` | 0.38944895839166466 |
| `assessment_history/6/raw_gap` | 0.012489964366282705 |
| `assessment_history/6/withdrawal` | — |
| `assessment_history/7/contributes` | true |
| `assessment_history/7/elapsed_seconds` | 0.8476420000661165 |
| `assessment_history/7/objective` | 0.4019386920392066 |
| `assessment_history/7/raw_bracket` | 0.4011111887161824 |
| `assessment_history/7/raw_gap` | 0.0008275033573103914 |
| `assessment_history/7/withdrawal` | — |
| `assessment_history/8/contributes` | true |
| `assessment_history/8/elapsed_seconds` | 0.9625870999880135 |
| `assessment_history/8/objective` | 0.4019386549722289 |
| `assessment_history/8/raw_bracket` | 0.4013361780483779 |
| `assessment_history/8/raw_gap` | 0.0006024769307518257 |
| `assessment_history/8/withdrawal` | — |
| `assessment_history/9/contributes` | true |
| `assessment_history/9/elapsed_seconds` | 1.069547799997963 |
| `assessment_history/9/objective` | 0.4019386544284414 |
| `assessment_history/9/raw_bracket` | 0.4017486577000748 |
| `assessment_history/9/raw_gap` | 0.00019000032208549202 |
| `assessment_history/9/withdrawal` | — |
| `attempts/0/iterations` | 10 |
| `attempts/0/method` | fw |
| `attempts/0/termination` | budget_exhausted |
| `best_contributing_candidate` | an object of 5 fields (10,979 characters); not shown, see the record |
| `budget_seconds` | — |
| `gap_target` | 1e-10 |
| `iteration_unit` | fw_iteration |
| `max_iterations` | 10 |
| `method` | fw |
| `policy` | explicit-v1 |
| `preparation_seconds` | 2.0192807000130415 |
| `solver_seconds` | 1.11694980005268 |
| `termination` | budget_exhausted |

## <a id="p-.payload.stages.key_rate.security_gates.accumulation_branch"></a>/payload/stages/key_rate/security_gates/accumulation_branch

`thm:accumulated-entropy`

## <a id="p-.payload.stages.key_rate.security_gates.key_length_permitted"></a>/payload/stages/key_rate/security_gates/key_length_permitted

`true`

## <a id="p-.payload.stages.key_rate.security_gates.source_mode"></a>/payload/stages/key_rate/security_gates/source_mode

`untrusted`

## <a id="p-.payload.stages.key_rate.solver_request"></a>/payload/stages/key_rate/solver_request

| Field | Value |
| --- | --- |
| `budget_seconds` | — |
| `certified_evaluation` | on |
| `gap_target` | 1e-10 |
| `max_iterations` | 10 |
| `method` | fw |
| `oracle` | qics |
| `warm_start` | — |

## <a id="p-.payload.stages.key_rate.solver_status"></a>/payload/stages/key_rate/solver_status

`iteration-limit`

## <a id="p-.payload.stages.receiver_construction"></a>/payload/stages/receiver_construction

| Field | Value |
| --- | --- |
| `assumption_ledger` | — |
| `assumptions` | — |
| `block_dimensions` | — |
| `bound_evaluation` | — |
| `calibration_coverage` | — |
| `coarse_graining` | — |
| `dark_count_route` | — |
| `declared_povm/factors/0/label` | alice_station |
| `declared_povm/factors/0/members/(A,gen)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(A,gen)/C:A` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(A,gen)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,gen)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,gen)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,gen)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,gen)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(A,test)/C:A` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(A,test)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(A,test)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(D,gen)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:D` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(D,gen)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,gen)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(D,test)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:D` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(D,test)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(D,test)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(H,gen)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:H` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(H,gen)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,gen)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(H,test)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:H` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(H,test)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(H,test)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(V,gen)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:V` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(V,gen)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,gen)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(V,test)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:V` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(V,test)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(V,test)/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(mc,gen)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(mc,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(mc,gen)/C:A` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(mc,gen)/C:D` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(mc,gen)/C:H` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(mc,gen)/C:V` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(mc,gen)/C:mc` | 1 × 1 matrix: 0.875 |
| `declared_povm/factors/0/members/(mc,gen)/C:nc` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(mc,test)/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(mc,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(mc,test)/C:A` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(mc,test)/C:D` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(mc,test)/C:H` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(mc,test)/C:V` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(mc,test)/C:mc` | 1 × 1 matrix: 0.125 |
| `declared_povm/factors/0/members/(mc,test)/C:nc` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/members/(nc,gen)/C:0` | 1 × 1 matrix: 0.875 |
| `declared_povm/factors/0/members/(nc,gen)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(nc,gen)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,gen)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,gen)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,gen)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,gen)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,gen)/C:nc` | 1 × 1 matrix: 0.4375 |
| `declared_povm/factors/0/members/(nc,test)/C:0` | 1 × 1 matrix: 0.125 |
| `declared_povm/factors/0/members/(nc,test)/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/0/members/(nc,test)/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,test)/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,test)/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,test)/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,test)/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/0/members/(nc,test)/C:nc` | 1 × 1 matrix: 0.0625 |
| `declared_povm/factors/0/party` | A |
| `declared_povm/factors/1/label` | bob_station |
| `declared_povm/factors/1/members/A/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/A/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/A/C:A` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/A/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/A/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/A/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/A/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/A/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/D/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:D` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/D/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/D/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/H/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:H` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/H/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/H/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/V/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:V` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/V/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/V/C:nc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/mc/C:0` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/mc/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/mc/C:A` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/mc/C:D` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/mc/C:H` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/mc/C:V` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/mc/C:mc` | 1 × 1 matrix: 1 |
| `declared_povm/factors/1/members/mc/C:nc` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/members/nc/C:0` | 1 × 1 matrix: 1 |
| `declared_povm/factors/1/members/nc/C:1` | 2 × 2 matrix, shown below |
| `declared_povm/factors/1/members/nc/C:A` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/nc/C:D` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/nc/C:H` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/nc/C:V` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/nc/C:mc` | 1 × 1 matrix: 0 |
| `declared_povm/factors/1/members/nc/C:nc` | 1 × 1 matrix: 0.5 |
| `declared_povm/factors/1/party` | B |
| `edges` | — |
| `efficiency_normalization` | — |
| `elements` | — |
| `modes` | — |
| `photon_cutoff` | — |
| `port_map` | — |
| `probe_alphabet` | — |
| `receiver_route` | element-graph |
| `refused` | false |
| `residuals` | — |
| `route` | declared_finite_povm |
| `rows_adaptation` | — |

*declared_povm/factors/0/members/(A,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21875 | -0.21875 |
| **2** | -0.21875 | 0.21875 |

*declared_povm/factors/0/members/(A,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.03125 | -0.03125 |
| **2** | -0.03125 | 0.03125 |

*declared_povm/factors/0/members/(D,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21875 | 0.21875 |
| **2** | 0.21875 | 0.21875 |

*declared_povm/factors/0/members/(D,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.03125 | 0.03125 |
| **2** | 0.03125 | 0.03125 |

*declared_povm/factors/0/members/(H,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.4375 |

*declared_povm/factors/0/members/(H,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.0625 |

*declared_povm/factors/0/members/(V,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.4375 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/0/members/(V,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.0625 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/0/members/(mc,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/0/members/(mc,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/0/members/(nc,gen)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/0/members/(nc,test)/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/1/members/A/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 |
| **2** | -0.25 | 0.25 |

*declared_povm/factors/1/members/D/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 |
| **2** | 0.25 | 0.25 |

*declared_povm/factors/1/members/H/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*declared_povm/factors/1/members/V/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/1/members/mc/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*declared_povm/factors/1/members/nc/C:1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.receiver_construction.receiver_route"></a>/payload/stages/receiver_construction/receiver_route

`element-graph`

## <a id="p-.payload.stages.receiver_construction.route"></a>/payload/stages/receiver_construction/route

`declared_finite_povm`

## <a id="p-.payload.stages.stations"></a>/payload/stages/stations

| Field | Value |
| --- | --- |
| `0` | an object of 7 fields (44,415 characters); not shown, see the record |
| `1` | an object of 7 fields (44,187 characters); not shown, see the record |

## <a id="p-.payload.stages.stations.0"></a>/payload/stages/stations/0

| Field | Value |
| --- | --- |
| `factor` | alice_station |
| `index` | 0 |
| `party` | A |
| `receiver` | an object of 15 fields (16,602 characters); not shown, see the record |
| `receiver_route` | element-graph |
| `reduction` | an object of 20 fields (21,716 characters); not shown, see the record |
| `rows_adaptation` | an object of 8 fields (5,959 characters); not shown, see the record |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.blocks"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/blocks

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 1 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 0 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 0 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 0 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 0 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 0 |
| `0/elements/5/letter` | mc |
| `0/photons` | 0 |
| `1/elements/0/block` | 2 × 2 matrix, shown below |
| `1/elements/0/letter` | nc |
| `1/elements/1/block` | 2 × 2 matrix, shown below |
| `1/elements/1/letter` | H |
| `1/elements/2/block` | 2 × 2 matrix, shown below |
| `1/elements/2/letter` | V |
| `1/elements/3/block` | 2 × 2 matrix, shown below |
| `1/elements/3/letter` | D |
| `1/elements/4/block` | 2 × 2 matrix, shown below |
| `1/elements/4/letter` | A |
| `1/elements/5/block` | 2 × 2 matrix, shown below |
| `1/elements/5/letter` | mc |
| `1/photons` | 1 |

*1/elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.blocks.0"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/blocks/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 1 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 0 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 0 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 0 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 0 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 0 |
| `elements/5/letter` | mc |
| `photons` | 0 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.blocks.1"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/blocks/1

| Field | Value |
| --- | --- |
| `elements/0/block` | 2 × 2 matrix, shown below |
| `elements/0/letter` | nc |
| `elements/1/block` | 2 × 2 matrix, shown below |
| `elements/1/letter` | H |
| `elements/2/block` | 2 × 2 matrix, shown below |
| `elements/2/letter` | V |
| `elements/3/block` | 2 × 2 matrix, shown below |
| `elements/3/letter` | D |
| `elements/4/block` | 2 × 2 matrix, shown below |
| `elements/4/letter` | A |
| `elements/5/block` | 2 × 2 matrix, shown below |
| `elements/5/letter` | mc |
| `photons` | 1 |

*elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/dark_composed

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 1 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 0 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 0 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 0 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 0 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 0 |
| `0/elements/5/letter` | mc |
| `0/photons` | 0 |
| `1/elements/0/block` | 2 × 2 matrix, shown below |
| `1/elements/0/letter` | nc |
| `1/elements/1/block` | 2 × 2 matrix, shown below |
| `1/elements/1/letter` | H |
| `1/elements/2/block` | 2 × 2 matrix, shown below |
| `1/elements/2/letter` | V |
| `1/elements/3/block` | 2 × 2 matrix, shown below |
| `1/elements/3/letter` | D |
| `1/elements/4/block` | 2 × 2 matrix, shown below |
| `1/elements/4/letter` | A |
| `1/elements/5/block` | 2 × 2 matrix, shown below |
| `1/elements/5/letter` | mc |
| `1/photons` | 1 |

*1/elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed.0"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/dark_composed/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 1 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 0 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 0 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 0 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 0 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 0 |
| `elements/5/letter` | mc |
| `photons` | 0 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed.1"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/dark_composed/1

| Field | Value |
| --- | --- |
| `elements/0/block` | 2 × 2 matrix, shown below |
| `elements/0/letter` | nc |
| `elements/1/block` | 2 × 2 matrix, shown below |
| `elements/1/letter` | H |
| `elements/2/block` | 2 × 2 matrix, shown below |
| `elements/2/letter` | V |
| `elements/3/block` | 2 × 2 matrix, shown below |
| `elements/3/letter` | D |
| `elements/4/block` | 2 × 2 matrix, shown below |
| `elements/4/letter` | A |
| `elements/5/block` | 2 × 2 matrix, shown below |
| `elements/5/letter` | mc |
| `photons` | 1 |

*elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.0.reduction.target_povm"></a>/payload/stages/stations/0/reduction/target_povm

| Field | Value |
| --- | --- |
| `A/0` | 1 × 1 matrix: 0 |
| `A/1` | 2 × 2 matrix, shown below |
| `A/2` | 1 × 1 matrix: 0 |
| `A/3` | 1 × 1 matrix: 0 |
| `A/4` | 1 × 1 matrix: 0 |
| `A/5` | 1 × 1 matrix: 0 |
| `A/6` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `A/7` | 1 × 1 matrix: 0 |
| `D/0` | 1 × 1 matrix: 0 |
| `D/1` | 2 × 2 matrix, shown below |
| `D/2` | 1 × 1 matrix: 0 |
| `D/3` | 1 × 1 matrix: 0 |
| `D/4` | 1 × 1 matrix: 0 |
| `D/5` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `D/6` | 1 × 1 matrix: 0 |
| `D/7` | 1 × 1 matrix: 0 |
| `H/0` | 1 × 1 matrix: 0 |
| `H/1` | 2 × 2 matrix, shown below |
| `H/2` | 1 × 1 matrix: 0 |
| `H/3` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `H/4` | 1 × 1 matrix: 0 |
| `H/5` | 1 × 1 matrix: 0 |
| `H/6` | 1 × 1 matrix: 0 |
| `H/7` | 1 × 1 matrix: 0 |
| `V/0` | 1 × 1 matrix: 0 |
| `V/1` | 2 × 2 matrix, shown below |
| `V/2` | 1 × 1 matrix: 0 |
| `V/3` | 1 × 1 matrix: 0 |
| `V/4` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `V/5` | 1 × 1 matrix: 0 |
| `V/6` | 1 × 1 matrix: 0 |
| `V/7` | 1 × 1 matrix: 0 |
| `mc/0` | 1 × 1 matrix: 0 |
| `mc/1` | 2 × 2 matrix, shown below |
| `mc/2` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/3` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/4` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/5` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/6` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/7` | 1 × 1 matrix: 1 |
| `nc/0` | 1 × 1 matrix: 1 |
| `nc/1` | 2 × 2 matrix, shown below |
| `nc/2` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `nc/3` | 1 × 1 matrix: 0 |
| `nc/4` | 1 × 1 matrix: 0 |
| `nc/5` | 1 × 1 matrix: 0 |
| `nc/6` | 1 × 1 matrix: 0 |
| `nc/7` | 1 × 1 matrix: 0 |

*A/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/4 | -1/4 |
| **2** | -1/4 | 1/4 |

*D/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/4 | 1/4 |
| **2** | 1/4 | 1/4 |

*H/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 1/2 |

*V/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/2 | 0 |
| **2** | 0 | 0 |

*mc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*nc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.0"></a>/payload/stages/stations/0/rows_adaptation/measurement_snaps/0/blocks/0

| Field | Value |
| --- | --- |
| `block` | m=0 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 0.0 |
| `displacement_squared` | 0 |
| `evaluated_off_snap` | false |
| `fix` | — |
| `group` | — |
| `group_fix` | — |
| `handed_reference/input_radius` | — |
| `handed_reference/kind` | exact |
| `handed_reference/largest_radius` | 0 |
| `handed_reference_kind` | exact |
| `lift_weight` | — |
| `pre_snap/completeness_residue` | 0.0 |
| `pre_snap/hermiticity_defect` | 0.0 |
| `pre_snap/min_eigenvalue_defect` | 0.0 |
| `receiver_fix` | — |
| `reference_kind` | exact |
| `residue_placement` | \[\] |
| `rests_on_assumption` | false |
| `status` | kept |
| `steps` | keep, decide-last |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.1"></a>/payload/stages/stations/0/rows_adaptation/measurement_snaps/0/blocks/1

| Field | Value |
| --- | --- |
| `block` | m=1 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 0.0 |
| `displacement_squared` | 0 |
| `evaluated_off_snap` | false |
| `fix` | — |
| `group` | — |
| `group_fix` | — |
| `handed_reference/input_radius` | — |
| `handed_reference/kind` | exact |
| `handed_reference/largest_radius` | 0 |
| `handed_reference_kind` | exact |
| `lift_weight` | — |
| `pre_snap/completeness_residue` | 0.0 |
| `pre_snap/hermiticity_defect` | 0.0 |
| `pre_snap/min_eigenvalue_defect` | 0.0 |
| `receiver_fix` | — |
| `reference_kind` | exact |
| `residue_placement` | \[\] |
| `rests_on_assumption` | false |
| `status` | kept |
| `steps` | keep, decide-last |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.1"></a>/payload/stages/stations/1

| Field | Value |
| --- | --- |
| `factor` | bob_station |
| `index` | 1 |
| `party` | B |
| `receiver` | an object of 15 fields (16,602 characters); not shown, see the record |
| `receiver_route` | element-graph |
| `reduction` | an object of 20 fields (21,492 characters); not shown, see the record |
| `rows_adaptation` | an object of 8 fields (5,957 characters); not shown, see the record |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.blocks"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/blocks

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 1 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 0 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 0 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 0 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 0 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 0 |
| `0/elements/5/letter` | mc |
| `0/photons` | 0 |
| `1/elements/0/block` | 2 × 2 matrix, shown below |
| `1/elements/0/letter` | nc |
| `1/elements/1/block` | 2 × 2 matrix, shown below |
| `1/elements/1/letter` | H |
| `1/elements/2/block` | 2 × 2 matrix, shown below |
| `1/elements/2/letter` | V |
| `1/elements/3/block` | 2 × 2 matrix, shown below |
| `1/elements/3/letter` | D |
| `1/elements/4/block` | 2 × 2 matrix, shown below |
| `1/elements/4/letter` | A |
| `1/elements/5/block` | 2 × 2 matrix, shown below |
| `1/elements/5/letter` | mc |
| `1/photons` | 1 |

*1/elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.blocks.0"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/blocks/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 1 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 0 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 0 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 0 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 0 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 0 |
| `elements/5/letter` | mc |
| `photons` | 0 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.blocks.1"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/blocks/1

| Field | Value |
| --- | --- |
| `elements/0/block` | 2 × 2 matrix, shown below |
| `elements/0/letter` | nc |
| `elements/1/block` | 2 × 2 matrix, shown below |
| `elements/1/letter` | H |
| `elements/2/block` | 2 × 2 matrix, shown below |
| `elements/2/letter` | V |
| `elements/3/block` | 2 × 2 matrix, shown below |
| `elements/3/letter` | D |
| `elements/4/block` | 2 × 2 matrix, shown below |
| `elements/4/letter` | A |
| `elements/5/block` | 2 × 2 matrix, shown below |
| `elements/5/letter` | mc |
| `photons` | 1 |

*elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.dark_composed"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/dark_composed

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 1 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 0 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 0 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 0 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 0 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 0 |
| `0/elements/5/letter` | mc |
| `0/photons` | 0 |
| `1/elements/0/block` | 2 × 2 matrix, shown below |
| `1/elements/0/letter` | nc |
| `1/elements/1/block` | 2 × 2 matrix, shown below |
| `1/elements/1/letter` | H |
| `1/elements/2/block` | 2 × 2 matrix, shown below |
| `1/elements/2/letter` | V |
| `1/elements/3/block` | 2 × 2 matrix, shown below |
| `1/elements/3/letter` | D |
| `1/elements/4/block` | 2 × 2 matrix, shown below |
| `1/elements/4/letter` | A |
| `1/elements/5/block` | 2 × 2 matrix, shown below |
| `1/elements/5/letter` | mc |
| `1/photons` | 1 |

*1/elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.dark_composed.0"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/dark_composed/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 1 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 0 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 0 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 0 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 0 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 0 |
| `elements/5/letter` | mc |
| `photons` | 0 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.dark_composed.1"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/dark_composed/1

| Field | Value |
| --- | --- |
| `elements/0/block` | 2 × 2 matrix, shown below |
| `elements/0/letter` | nc |
| `elements/1/block` | 2 × 2 matrix, shown below |
| `elements/1/letter` | H |
| `elements/2/block` | 2 × 2 matrix, shown below |
| `elements/2/letter` | V |
| `elements/3/block` | 2 × 2 matrix, shown below |
| `elements/3/letter` | D |
| `elements/4/block` | 2 × 2 matrix, shown below |
| `elements/4/letter` | A |
| `elements/5/block` | 2 × 2 matrix, shown below |
| `elements/5/letter` | mc |
| `photons` | 1 |

*elements/0/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -2.22045e-16 | -6.16298e-33i |
| **2** | 6.16298e-33i | -2.22045e-16 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0.5 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.5 | 0 |
| **2** | 0 | 0 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | 0.25 + 2.16489e-17i |
| **2** | 0.25 − 2.16489e-17i | 0.25 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.25 | -0.25 − 2.16489e-17i |
| **2** | -0.25 + 2.16489e-17i | 0.25 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.1.reduction.target_povm"></a>/payload/stages/stations/1/reduction/target_povm

| Field | Value |
| --- | --- |
| `A/0` | 1 × 1 matrix: 0 |
| `A/1` | 2 × 2 matrix, shown below |
| `A/2` | 1 × 1 matrix: 0 |
| `A/3` | 1 × 1 matrix: 0 |
| `A/4` | 1 × 1 matrix: 0 |
| `A/5` | 1 × 1 matrix: 0 |
| `A/6` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `A/7` | 1 × 1 matrix: 0 |
| `D/0` | 1 × 1 matrix: 0 |
| `D/1` | 2 × 2 matrix, shown below |
| `D/2` | 1 × 1 matrix: 0 |
| `D/3` | 1 × 1 matrix: 0 |
| `D/4` | 1 × 1 matrix: 0 |
| `D/5` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `D/6` | 1 × 1 matrix: 0 |
| `D/7` | 1 × 1 matrix: 0 |
| `H/0` | 1 × 1 matrix: 0 |
| `H/1` | 2 × 2 matrix, shown below |
| `H/2` | 1 × 1 matrix: 0 |
| `H/3` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `H/4` | 1 × 1 matrix: 0 |
| `H/5` | 1 × 1 matrix: 0 |
| `H/6` | 1 × 1 matrix: 0 |
| `H/7` | 1 × 1 matrix: 0 |
| `V/0` | 1 × 1 matrix: 0 |
| `V/1` | 2 × 2 matrix, shown below |
| `V/2` | 1 × 1 matrix: 0 |
| `V/3` | 1 × 1 matrix: 0 |
| `V/4` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `V/5` | 1 × 1 matrix: 0 |
| `V/6` | 1 × 1 matrix: 0 |
| `V/7` | 1 × 1 matrix: 0 |
| `mc/0` | 1 × 1 matrix: 0 |
| `mc/1` | 2 × 2 matrix, shown below |
| `mc/2` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/3` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/4` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/5` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/6` | 1 × 1 matrix: ≈ 0.5 (549755813887/1099511627776) |
| `mc/7` | 1 × 1 matrix: 1 |
| `nc/0` | 1 × 1 matrix: 1 |
| `nc/1` | 2 × 2 matrix, shown below |
| `nc/2` | 1 × 1 matrix: ≈ 0.5 (549755813889/1099511627776) |
| `nc/3` | 1 × 1 matrix: 0 |
| `nc/4` | 1 × 1 matrix: 0 |
| `nc/5` | 1 × 1 matrix: 0 |
| `nc/6` | 1 × 1 matrix: 0 |
| `nc/7` | 1 × 1 matrix: 0 |

*A/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/4 | -1/4 |
| **2** | -1/4 | 1/4 |

*D/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/4 | 1/4 |
| **2** | 1/4 | 1/4 |

*H/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 1/2 |

*V/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 1/2 | 0 |
| **2** | 0 | 0 |

*mc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

*nc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0 | 0 |
| **2** | 0 | 0 |

## <a id="p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.0"></a>/payload/stages/stations/1/rows_adaptation/measurement_snaps/0/blocks/0

| Field | Value |
| --- | --- |
| `block` | m=0 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 0.0 |
| `displacement_squared` | 0 |
| `evaluated_off_snap` | false |
| `fix` | — |
| `group` | — |
| `group_fix` | — |
| `handed_reference/input_radius` | — |
| `handed_reference/kind` | exact |
| `handed_reference/largest_radius` | 0 |
| `handed_reference_kind` | exact |
| `lift_weight` | — |
| `pre_snap/completeness_residue` | 0.0 |
| `pre_snap/hermiticity_defect` | 0.0 |
| `pre_snap/min_eigenvalue_defect` | 0.0 |
| `receiver_fix` | — |
| `reference_kind` | exact |
| `residue_placement` | \[\] |
| `rests_on_assumption` | false |
| `status` | kept |
| `steps` | keep, decide-last |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.1"></a>/payload/stages/stations/1/rows_adaptation/measurement_snaps/0/blocks/1

| Field | Value |
| --- | --- |
| `block` | m=1 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 0.0 |
| `displacement_squared` | 0 |
| `evaluated_off_snap` | false |
| `fix` | — |
| `group` | — |
| `group_fix` | — |
| `handed_reference/input_radius` | — |
| `handed_reference/kind` | exact |
| `handed_reference/largest_radius` | 0 |
| `handed_reference_kind` | exact |
| `lift_weight` | — |
| `pre_snap/completeness_residue` | 0.0 |
| `pre_snap/hermiticity_defect` | 0.0 |
| `pre_snap/min_eigenvalue_defect` | 0.0 |
| `receiver_fix` | — |
| `reference_kind` | exact |
| `residue_placement` | \[\] |
| `rests_on_assumption` | false |
| `status` | kept |
| `steps` | keep, decide-last |
| `support_not_preserved` | false |

## <a id="p-.payload.statistics_consistency"></a>/payload/statistics_consistency

| Field | Value |
| --- | --- |
| `alpha_0_rule` | fixed_order |
| `caller_constraint_entries` | 0 |
| `checked` | false |
| `honest_statistics_supplied` | false |
| `min_model_pass_probability` | 1/2 |
| `model_pass_decision` | — |
| `model_pass_exponent_bits` | — |
| `model_pass_exponent_tier` | — |
| `no_cap_reason` | — |
| `orders` | \[\] |
| `refused` | false |
| `rounds` | 100000000 |
| `solve` | — |
| `statistics_check` | on |
| `unchecked_premise` | A-REACH |
| `unchecked_reason` | out_of_scope |

## <a id="field-names"></a>What the field names mean

- `key_map`: each pair of readouts with the key holder's raw key bit; perp marks a round that gives no key bit.
- `key_holder`: the party (A or B) whose raw string both keys are computed from.
- `choice_weightings`: the public choices whose weights depend on a station's setting, one entry per weighted measurement.
- `source_alphabet`: in a choice weighting, the outcomes of the measurement the weighting is declared at.
- `setting_map`: in a choice weighting, the setting each of those outcomes belongs to.
- `source_mode`: whether the analysis trusts the source (trusted) or treats it as the attacker's (untrusted).
- `alice_dim`: the dimension of system A, the declaration's per-round letter on Alice's side.
- `alice_povm`: the measurement on system A of the declaration; with a trusted source, Alice's measurement in the source-replacement picture, one operator per signal, which selects the signal sent.
- `alice_marginal`: the reduced state of system A that the declaration fixes.
- `signal_alphabet`: the source's signals (its letters), in declared order.
- `virtual_transmitted_system`: the dimension of the transmitted system as the proof models it.
- `virtual_ensemble_weights`: the probability of each signal in the ensemble the proof models.
- `public_choices`: the public choices the compiled source declares: each one's party, choices and weights.
