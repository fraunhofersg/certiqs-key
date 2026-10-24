# Record excerpts

Every record value the key-rate report cites, once, under its JSON pointer (RFC 6901) from the record root, in the record's order. Report id 2fb6d5b7e8a4e8408f1f8ce77d793499932b205e9904788ed51cc86ff9869fa8. [Back to the report](report.md)

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

`A`

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
| `14/1` | 0 |
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
| `25/1` | 1 |
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
| `40/1` | 0 |
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
| `51/1` | 1 |
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

## <a id="p-.payload.composition_flow.stages.12.children.3.detail"></a>/payload/composition_flow/stages/12/children/3/detail

| Field | Value |
| --- | --- |
| `alpha` | 1.00435275282 |
| `chosen_alpha` | 1.00435275282 |
| `contradiction_alpha` | — |
| `contradiction_rule` | an evaluation refused with entropy_bound_above_key_ceiling proves that no feasible state of the declaration reproduces any accepted statistic (D_min > 0, meat-core/prop:value-range (i)-(ii)), which does not depend on alpha; the search stops there and the run refuses as a whole, with that evaluation's refusal and every evaluation made up to it |
| `evaluations/0/alpha` | 1.00001 |
| `evaluations/0/h_lb` | 0.022173977586348974 |
| `evaluations/0/h_low` | 0.022176449198268538 |
| `evaluations/0/key_length` | 0 |
| `evaluations/0/phase` | coarse |
| `evaluations/0/reason` | certified_reported |
| `evaluations/0/relative_gap` | 0.00011751067865757876 |
| `evaluations/0/score` | -2697580.3810124137 |
| `evaluations/0/seconds` | 63.22003740002401 |
| `evaluations/0/set_aside` | — |
| `evaluations/1/alpha` | 1.00007578583 |
| `evaluations/1/h_lb` | 0.022170574758793016 |
| `evaluations/1/h_low` | 0.022171137740138357 |
| `evaluations/1/key_length` | 0 |
| `evaluations/1/phase` | coarse |
| `evaluations/1/reason` | certified_reported |
| `evaluations/1/relative_gap` | 2.5118838835655202e-05 |
| `evaluations/1/score` | -93490.59358602762 |
| `evaluations/1/seconds` | 36.24621469993144 |
| `evaluations/1/set_aside` | — |
| `evaluations/2/alpha` | 1.00057434918 |
| `evaluations/2/h_lb` | 0.02212957459067009 |
| `evaluations/2/h_low` | 0.02213068305011337 |
| `evaluations/2/key_length` | 249431 |
| `evaluations/2/phase` | coarse |
| `evaluations/2/reason` | certified_reported |
| `evaluations/2/relative_gap` | 5.005095675984007e-05 |
| `evaluations/2/score` | 249431.0 |
| `evaluations/2/seconds` | 22.717906899983063 |
| `evaluations/2/set_aside` | — |
| `evaluations/3/alpha` | 1.00435275282 |
| `evaluations/3/h_lb` | 0.021811680981667834 |
| `evaluations/3/h_low` | 0.02181202355574533 |
| `evaluations/3/key_length` | 289368 |
| `evaluations/3/phase` | coarse |
| `evaluations/3/reason` | certified_reported |
| `evaluations/3/relative_gap` | 1.570091860707826e-05 |
| `evaluations/3/score` | 289368.0 |
| `evaluations/3/seconds` | 17.077435399987735 |
| `evaluations/3/set_aside` | — |
| `evaluations/4/alpha` | 1.03298769777 |
| `evaluations/4/h_lb` | 0.018945976585700842 |
| `evaluations/4/h_low` | 0.018946361836105055 |
| `evaluations/4/key_length` | 246634 |
| `evaluations/4/phase` | coarse |
| `evaluations/4/reason` | certified_reported |
| `evaluations/4/relative_gap` | 2.034087370287701e-05 |
| `evaluations/4/score` | 246634.0 |
| `evaluations/4/seconds` | 10.386745700030588 |
| `evaluations/4/set_aside` | — |
| `evaluations/5/alpha` | 1.25 |
| `evaluations/5/h_lb` | 0.00897192370687863 |
| `evaluations/5/h_low` | 0.008972089236669615 |
| `evaluations/5/key_length` | 77864 |
| `evaluations/5/phase` | coarse |
| `evaluations/5/reason` | certified_reported |
| `evaluations/5/relative_gap` | 1.8449161408776396e-05 |
| `evaluations/5/score` | 77864.0 |
| `evaluations/5/seconds` | 9.504157499992289 |
| `evaluations/5/set_aside` | — |
| `evaluations/6/alpha` | 1.00269849392 |
| `evaluations/6/h_lb` | 0.021953796214154987 |
| `evaluations/6/h_low` | 0.021954183820141356 |
| `evaluations/6/key_length` | 287559 |
| `evaluations/6/phase` | refine |
| `evaluations/6/reason` | certified_reported |
| `evaluations/6/relative_gap` | 1.764749529198988e-05 |
| `evaluations/6/score` | 287559.0 |
| `evaluations/6/seconds` | 12.263528699986637 |
| `evaluations/6/set_aside` | — |
| `evaluations/7/alpha` | 1.00702112275 |
| `evaluations/7/h_lb` | 0.021572784056513254 |
| `evaluations/7/h_low` | 0.02157397137555446 |
| `evaluations/7/key_length` | 287926 |
| `evaluations/7/phase` | refine |
| `evaluations/7/reason` | certified_reported |
| `evaluations/7/relative_gap` | 5.5031770934384137e-05 |
| `evaluations/7/score` | 287926.0 |
| `evaluations/7/seconds` | 10.953313699923456 |
| `evaluations/7/set_aside` | — |
| `evaluations/8/alpha` | 1.01267847112 |
| `evaluations/8/h_lb` | 0.02103411271537088 |
| `evaluations/8/h_low` | 0.021034466287732156 |
| `evaluations/8/key_length` | 280675 |
| `evaluations/8/phase` | refine |
| `evaluations/8/reason` | certified_reported |
| `evaluations/8/relative_gap` | 1.6807469859925378e-05 |
| `evaluations/8/score` | 280675.0 |
| `evaluations/8/seconds` | 12.708188700024039 |
| `evaluations/8/set_aside` | — |
| `evaluations/9/alpha` | 1.00487283566 |
| `evaluations/9/h_lb` | 0.021766207428938908 |
| `evaluations/9/h_low` | 0.02176647264519413 |
| `evaluations/9/key_length` | 289330 |
| `evaluations/9/phase` | refine |
| `evaluations/9/reason` | certified_reported |
| `evaluations/9/relative_gap` | 1.2180338371341551e-05 |
| `evaluations/9/score` | 289330.0 |
| `evaluations/9/seconds` | 11.918911299901083 |
| `evaluations/9/set_aside` | — |
| `evaluations/10/alpha` | 1.00388817896 |
| `evaluations/10/h_lb` | 0.021851140099320165 |
| `evaluations/10/h_low` | 0.02185236592471818 |
| `evaluations/10/key_length` | 289215 |
| `evaluations/10/phase` | refine |
| `evaluations/10/reason` | certified_reported |
| `evaluations/10/relative_gap` | 5.609034896673432e-05 |
| `evaluations/10/score` | 289215.0 |
| `evaluations/10/seconds` | 13.708134400076233 |
| `evaluations/10/set_aside` | — |
| `h_lb` | 0.021811680981667834 |
| `h_low` | 0.02181202355574533 |
| `key_length` | 289368 |
| `no_positive_key` | — |
| `no_positive_key_rule` | where some evaluation formed a bound and none reported a positive key length, no alpha is chosen: the run reported is the evaluation with the largest h_low (a tie to the first evaluated; with no finite h_low, the highest score), and the largest h_lb the search saw, with the largest bound on the declaration the solve searched where the reported h_lb is the reference companion's, is recorded as a diagnostic beside why the key is 0 |
| `reads` | the honest model at fixed configuration; no observed data |
| `refinement_stopped` | — |
| `rule` | coarse log grid in alpha - 1, then golden-section in log(alpha - 1) |
| `searched` | true |
| `set_aside_rule` | an evaluation with a key length is set aside when its relative gap (h_low - h_lb)/\|h_low\| on the declaration the solve searched (h_lb there being the run's reference_bracket.snapped.h_lb where the reference bound is counted) exceeds 0.001 (or the run's gap target over \|h_low\|, where larger) and 10 times the median relative gap of the search's other evaluations (the coarse grid judged when complete, a refinement evaluation against those before it); its certified score is a lower bound, so it centres the refinement where it is the best coarse score and takes part in a golden-section comparison it wins or ties, and a comparison it would lose stops the refinement; its key length stays eligible for the choice |
| `settings/coarse_points` | 6 |
| `settings/lower_alpha_minus_one` | 1e-05 |
| `settings/refine_steps` | 5 |
| `settings/upper_alpha_minus_one` | 0.25 |

## <a id="p-.payload.config"></a>/payload/config

| Field | Value |
| --- | --- |
| `alpha` | — |
| `alpha_search/coarse_points` | 6 |
| `alpha_search/lower_alpha_minus_one` | 1e-05 |
| `alpha_search/refine_steps` | 5 |
| `alpha_search/upper_alpha_minus_one` | 0.25 |
| `completeness_budget` | 1/1000000 |
| `config_digest` | c86817bdaa9ede07bb98060b2744dc5b4147e10a5fc0554c66ebf076b7332439 |
| `constrained` | — |
| `declared_tolerance` | 1e-12 |
| `device/acceptance_map` | pair-resolved |
| `device/alice_basis_split` | 14/25 |
| `device/alice_dark_count/A` | 13/100000000 |
| `device/alice_dark_count/D` | 13/100000000 |
| `device/alice_dark_count/H` | 13/100000000 |
| `device/alice_dark_count/V` | 13/100000000 |
| `device/alice_efficiency/A` | 216/295 |
| `device/alice_efficiency/D` | 4/5 |
| `device/alice_efficiency/H` | 4/5 |
| `device/alice_efficiency/V` | 216/295 |
| `device/alice_exact_window` | 2 |
| `device/alice_half_wave_angle` | 1/8 |
| `device/alice_pbs_leak_reflected` | 1/100 |
| `device/alice_pbs_leak_transmitted` | 1/1000 |
| `device/alice_photon_cutoff` | 1 |
| `device/bob_basis_split` | 14/25 |
| `device/bob_dark_count/A` | 13/100000000 |
| `device/bob_dark_count/D` | 13/100000000 |
| `device/bob_dark_count/H` | 13/100000000 |
| `device/bob_dark_count/V` | 13/100000000 |
| `device/bob_efficiency/A` | 216/295 |
| `device/bob_efficiency/D` | 4/5 |
| `device/bob_efficiency/H` | 4/5 |
| `device/bob_efficiency/V` | 216/295 |
| `device/bob_exact_window` | 2 |
| `device/bob_half_wave_angle` | 15288567027608731/113187804032455040 |
| `device/bob_pbs_leak_reflected` | 1/100 |
| `device/bob_pbs_leak_transmitted` | 1/1000 |
| `device/bob_photon_cutoff` | 1 |
| `device/key_bases` | ZX |
| `device/party_local_view` | operator |
| `device/route` | encoded |
| `device/source_model` | ideal_pair |
| `device/test_fraction` | 1/8 |
| `endpoint_rule` | bernstein |
| `model/alice_transmittance` | 5696652996790543/18014398509481984 |
| `model/bob_transmittance` | 5696652996790543/18014398509481984 |
| `model/mean_pairs` | 1/32 |
| `model/visibility` | 49/50 |
| `parameters/alpha` | 1.05 |
| `parameters/eps_auth` | 0.0 |
| `parameters/eps_ev` | 9.313225746154785e-10 |
| `parameters/eps_pa` | 9.313225746154785e-10 |
| `parameters/k_auth` | 0 |
| `parameters/lambda_ec` | 74479 |
| `parameters/min_model_pass_probability` | 1/2 |
| `parameters/reference_enclosure` | true |
| `parameters/statistics_check` | on |
| `parameters/strict_snaps` | false |
| `rounds` | 17000000 |
| `solver/budget_seconds` | 600 |
| `solver/max_iterations` | — |
| `solver/method` | auto |
| `tail_evaluation` | sweep |

## <a id="p-.payload.config.alpha"></a>/payload/config/alpha

`—`

## <a id="p-.payload.config.alpha_search.coarse_points"></a>/payload/config/alpha_search/coarse_points

`6`

## <a id="p-.payload.config.alpha_search.lower_alpha_minus_one"></a>/payload/config/alpha_search/lower_alpha_minus_one

`1e-05`

## <a id="p-.payload.config.alpha_search.refine_steps"></a>/payload/config/alpha_search/refine_steps

`5`

## <a id="p-.payload.config.alpha_search.upper_alpha_minus_one"></a>/payload/config/alpha_search/upper_alpha_minus_one

`0.25`

## <a id="p-.payload.config.completeness_budget"></a>/payload/config/completeness_budget

`1/1000000`

## <a id="p-.payload.config.constrained"></a>/payload/config/constrained

`—`

## <a id="p-.payload.config.declared_tolerance"></a>/payload/config/declared_tolerance

`1e-12`

## <a id="p-.payload.config.device.acceptance_map"></a>/payload/config/device/acceptance_map

`pair-resolved`

## <a id="p-.payload.config.device.alice_basis_split"></a>/payload/config/device/alice_basis_split

`14/25`

## <a id="p-.payload.config.device.alice_dark_count"></a>/payload/config/device/alice_dark_count

| Field | Value |
| --- | --- |
| `A` | 13/100000000 |
| `D` | 13/100000000 |
| `H` | 13/100000000 |
| `V` | 13/100000000 |

## <a id="p-.payload.config.device.alice_efficiency"></a>/payload/config/device/alice_efficiency

| Field | Value |
| --- | --- |
| `A` | 216/295 |
| `D` | 4/5 |
| `H` | 4/5 |
| `V` | 216/295 |

## <a id="p-.payload.config.device.alice_exact_window"></a>/payload/config/device/alice_exact_window

`2`

## <a id="p-.payload.config.device.alice_half_wave_angle"></a>/payload/config/device/alice_half_wave_angle

`1/8`

## <a id="p-.payload.config.device.alice_pbs_leak_reflected"></a>/payload/config/device/alice_pbs_leak_reflected

`1/100`

## <a id="p-.payload.config.device.alice_pbs_leak_transmitted"></a>/payload/config/device/alice_pbs_leak_transmitted

`1/1000`

## <a id="p-.payload.config.device.alice_photon_cutoff"></a>/payload/config/device/alice_photon_cutoff

`1`

## <a id="p-.payload.config.device.bob_basis_split"></a>/payload/config/device/bob_basis_split

`14/25`

## <a id="p-.payload.config.device.bob_dark_count"></a>/payload/config/device/bob_dark_count

| Field | Value |
| --- | --- |
| `A` | 13/100000000 |
| `D` | 13/100000000 |
| `H` | 13/100000000 |
| `V` | 13/100000000 |

## <a id="p-.payload.config.device.bob_efficiency"></a>/payload/config/device/bob_efficiency

| Field | Value |
| --- | --- |
| `A` | 216/295 |
| `D` | 4/5 |
| `H` | 4/5 |
| `V` | 216/295 |

## <a id="p-.payload.config.device.bob_exact_window"></a>/payload/config/device/bob_exact_window

`2`

## <a id="p-.payload.config.device.bob_half_wave_angle"></a>/payload/config/device/bob_half_wave_angle

`15288567027608731/113187804032455040`

## <a id="p-.payload.config.device.bob_pbs_leak_reflected"></a>/payload/config/device/bob_pbs_leak_reflected

`1/100`

## <a id="p-.payload.config.device.bob_pbs_leak_transmitted"></a>/payload/config/device/bob_pbs_leak_transmitted

`1/1000`

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

`5696652996790543/18014398509481984`

## <a id="p-.payload.config.model.bob_transmittance"></a>/payload/config/model/bob_transmittance

`5696652996790543/18014398509481984`

## <a id="p-.payload.config.model.mean_pairs"></a>/payload/config/model/mean_pairs

`1/32`

## <a id="p-.payload.config.model.visibility"></a>/payload/config/model/visibility

`49/50`

## <a id="p-.payload.config.parameters"></a>/payload/config/parameters

| Field | Value |
| --- | --- |
| `alpha` | 1.05 |
| `eps_auth` | 0.0 |
| `eps_ev` | 9.313225746154785e-10 |
| `eps_pa` | 9.313225746154785e-10 |
| `k_auth` | 0 |
| `lambda_ec` | 74479 |
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

`74479`

## <a id="p-.payload.config.parameters.min_model_pass_probability"></a>/payload/config/parameters/min_model_pass_probability

`1/2`

## <a id="p-.payload.config.parameters.reference_enclosure"></a>/payload/config/parameters/reference_enclosure

`true`

## <a id="p-.payload.config.parameters.statistics_check"></a>/payload/config/parameters/statistics_check

`on`

## <a id="p-.payload.config.parameters.strict_snaps"></a>/payload/config/parameters/strict_snaps

`false`

## <a id="p-.payload.config.rounds"></a>/payload/config/rounds

`17000000`

## <a id="p-.payload.config.solver.budget_seconds"></a>/payload/config/solver/budget_seconds

`600`

## <a id="p-.payload.config.solver.max_iterations"></a>/payload/config/solver/max_iterations

`—`

## <a id="p-.payload.config.solver.method"></a>/payload/config/solver/method

`auto`

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
| `instance` | an object of 2 fields (13,689 characters); not shown, see the record |
| `producer` | — |
| `reference_companion` | an object of 11 fields (7,726 characters); not shown, see the record |
| `snap_max_defect` | 3.5879912696449335e-07 |
| `snap_max_displacement` | 1.7598295477055413e-12 |

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
| `box/gen/lower` | 219617/8500000 |
| `box/gen/upper` | 447323/17000000 |
| `box/gen:X\|A/lower` | 0 |
| `box/gen:X\|A/upper` | 0 |
| `box/gen:X\|D/lower` | 0 |
| `box/gen:X\|D/upper` | 0 |
| `box/gen:X\|H/lower` | 0 |
| `box/gen:X\|H/upper` | 0 |
| `box/gen:X\|V/lower` | 0 |
| `box/gen:X\|V/upper` | 0 |
| `box/gen:X\|Z/lower` | 212107/17000000 |
| `box/gen:X\|Z/upper` | 108891/8500000 |
| `box/gen:X\|mc/lower` | 0 |
| `box/gen:X\|mc/upper` | 7/8500000 |
| `box/gen:X\|nc/lower` | 597169/8500000 |
| `box/gen:X\|nc/upper` | 603667/8500000 |
| `box/gen:Z\|A/lower` | 0 |
| `box/gen:Z\|A/upper` | 0 |
| `box/gen:Z\|D/lower` | 0 |
| `box/gen:Z\|D/upper` | 0 |
| `box/gen:Z\|H/lower` | 0 |
| `box/gen:Z\|H/upper` | 0 |
| `box/gen:Z\|V/lower` | 0 |
| `box/gen:Z\|V/upper` | 0 |
| `box/gen:Z\|X/lower` | 26507/2125000 |
| `box/gen:Z\|X/upper` | 21773/1700000 |
| `box/gen:Z\|mc/lower` | 0 |
| `box/gen:Z\|mc/upper` | 7/8500000 |
| `box/gen:Z\|nc/lower` | 76051/850000 |
| `box/gen:Z\|nc/upper` | 1535527/17000000 |
| `box/gen:mc\|A/lower` | 0 |
| `box/gen:mc\|A/upper` | 0 |
| `box/gen:mc\|D/lower` | 0 |
| `box/gen:mc\|D/upper` | 0 |
| `box/gen:mc\|H/lower` | 0 |
| `box/gen:mc\|H/upper` | 0 |
| `box/gen:mc\|V/lower` | 0 |
| `box/gen:mc\|V/upper` | 0 |
| `box/gen:mc\|X/lower` | 0 |
| `box/gen:mc\|X/upper` | 7/8500000 |
| `box/gen:mc\|Z/lower` | 0 |
| `box/gen:mc\|Z/upper` | 7/8500000 |
| `box/gen:mc\|mc/lower` | 0 |
| `box/gen:mc\|mc/upper` | 13/17000000 |
| `box/gen:mc\|nc/lower` | 0 |
| `box/gen:mc\|nc/upper` | 1/1000000 |
| `box/gen:nc\|A/lower` | 0 |
| `box/gen:nc\|A/upper` | 0 |
| `box/gen:nc\|D/lower` | 0 |
| `box/gen:nc\|D/upper` | 0 |
| `box/gen:nc\|H/lower` | 0 |
| `box/gen:nc\|H/upper` | 0 |
| `box/gen:nc\|V/lower` | 0 |
| `box/gen:nc\|V/upper` | 0 |
| `box/gen:nc\|X/lower` | 1194389/17000000 |
| `box/gen:nc\|X/upper` | 241477/3400000 |
| `box/gen:nc\|Z/lower` | 1520969/17000000 |
| `box/gen:nc\|Z/upper` | 383869/4250000 |
| `box/gen:nc\|mc/lower` | 0 |
| `box/gen:nc\|mc/upper` | 1/1000000 |
| `box/gen:nc\|nc/lower` | 2132747/4250000 |
| `box/gen:nc\|nc/upper` | 534771/1062500 |
| `box/test:A\|A/lower` | 1021/1700000 |
| `box/test:A\|A/upper` | 719/1062500 |
| `box/test:A\|D/lower` | 183/17000000 |
| `box/test:A\|D/upper` | 3/125000 |
| `box/test:A\|H/lower` | 3561/8500000 |
| `box/test:A\|H/upper` | 2053/4250000 |
| `box/test:A\|V/lower` | 6619/17000000 |
| `box/test:A\|V/upper` | 7671/17000000 |
| `box/test:A\|X/lower` | 0 |
| `box/test:A\|X/upper` | 0 |
| `box/test:A\|Z/lower` | 0 |
| `box/test:A\|Z/upper` | 0 |
| `box/test:A\|mc/lower` | 0 |
| `box/test:A\|mc/upper` | 13/17000000 |
| `box/test:A\|nc/lower` | 4793/1000000 |
| `box/test:A\|nc/upper` | 10629/2125000 |
| `box/test:D\|A/lower` | 183/17000000 |
| `box/test:D\|A/upper` | 3/125000 |
| `box/test:D\|D/lower` | 1503/2125000 |
| `box/test:D\|D/upper` | 13423/17000000 |
| `box/test:D\|H/lower` | 7663/17000000 |
| `box/test:D\|H/upper` | 1099/2125000 |
| `box/test:D\|V/lower` | 3561/8500000 |
| `box/test:D\|V/upper` | 2053/4250000 |
| `box/test:D\|X/lower` | 0 |
| `box/test:D\|X/upper` | 0 |
| `box/test:D\|Z/lower` | 0 |
| `box/test:D\|Z/upper` | 0 |
| `box/test:D\|mc/lower` | 0 |
| `box/test:D\|mc/upper` | 13/17000000 |
| `box/test:D\|nc/lower` | 1351/265625 |
| `box/test:D\|nc/upper` | 90119/17000000 |
| `box/test:H\|A/lower` | 8019/17000000 |
| `box/test:H\|A/upper` | 9171/17000000 |
| `box/test:H\|D/lower` | 1337/3400000 |
| `box/test:H\|D/upper` | 3871/8500000 |
| `box/test:H\|H/lower` | 9901/8500000 |
| `box/test:H\|H/upper` | 10791/8500000 |
| `box/test:H\|V/lower` | 273/17000000 |
| `box/test:H\|V/upper` | 267/8500000 |
| `box/test:H\|X/lower` | 0 |
| `box/test:H\|X/upper` | 0 |
| `box/test:H\|Z/lower` | 0 |
| `box/test:H\|Z/upper` | 0 |
| `box/test:H\|mc/lower` | 0 |
| `box/test:H\|mc/upper` | 13/17000000 |
| `box/test:H\|nc/lower` | 110207/17000000 |
| `box/test:H\|nc/upper` | 28581/4250000 |
| `box/test:V\|A/lower` | 5801/17000000 |
| `box/test:V\|A/upper` | 679/1700000 |
| `box/test:V\|D/lower` | 8019/17000000 |
| `box/test:V\|D/upper` | 9171/17000000 |
| `box/test:V\|H/lower` | 273/17000000 |
| `box/test:V\|H/upper` | 267/8500000 |
| `box/test:V\|V/lower` | 263/265625 |
| `box/test:V\|V/upper` | 9239/8500000 |
| `box/test:V\|X/lower` | 0 |
| `box/test:V\|X/upper` | 0 |
| `box/test:V\|Z/lower` | 0 |
| `box/test:V\|Z/upper` | 0 |
| `box/test:V\|mc/lower` | 0 |
| `box/test:V\|mc/upper` | 13/17000000 |
| `box/test:V\|nc/lower` | 52029/8500000 |
| `box/test:V\|nc/upper` | 108061/17000000 |
| `box/test:mc\|A/lower` | 0 |
| `box/test:mc\|A/upper` | 13/17000000 |
| `box/test:mc\|D/lower` | 0 |
| `box/test:mc\|D/upper` | 13/17000000 |
| `box/test:mc\|H/lower` | 0 |
| `box/test:mc\|H/upper` | 13/17000000 |
| `box/test:mc\|V/lower` | 0 |
| `box/test:mc\|V/upper` | 13/17000000 |
| `box/test:mc\|X/lower` | 0 |
| `box/test:mc\|X/upper` | 0 |
| `box/test:mc\|Z/lower` | 0 |
| `box/test:mc\|Z/upper` | 0 |
| `box/test:mc\|mc/lower` | 0 |
| `box/test:mc\|mc/upper` | 13/17000000 |
| `box/test:mc\|nc/lower` | 0 |
| `box/test:mc\|nc/upper` | 7/8500000 |
| `box/test:nc\|A/lower` | 81403/17000000 |
| `box/test:nc\|A/upper` | 84953/17000000 |
| `box/test:nc\|D/lower` | 86549/17000000 |
| `box/test:nc\|D/upper` | 45103/8500000 |
| `box/test:nc\|H/lower` | 55061/8500000 |
| `box/test:nc\|H/upper` | 57119/8500000 |
| `box/test:nc\|V/lower` | 20827/3400000 |
| `box/test:nc\|V/upper` | 5407/850000 |
| `box/test:nc\|X/lower` | 0 |
| `box/test:nc\|X/upper` | 0 |
| `box/test:nc\|Z/lower` | 0 |
| `box/test:nc\|Z/upper` | 0 |
| `box/test:nc\|mc/lower` | 0 |
| `box/test:nc\|mc/upper` | 7/8500000 |
| `box/test:nc\|nc/lower` | 151747/2125000 |
| `box/test:nc\|nc/upper` | 122707/1700000 |
| `completeness_certified` | 1/1000000 |
| `completeness_exact` | false |
| `endpoint_rule` | bernstein |
| `geometry` | PolytopeGeometry |
| `honest_distribution` | an object of 79 fields (7,184 characters); not shown, see the record |
| `outcomes` | gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:Z\|H, gen:Z\|V, gen:Z\|D, gen:Z\|A, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:X\|H, gen:X\|V, gen:X\|D, gen:X\|A, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:nc\|H, gen:nc\|V, gen:nc\|D, gen:nc\|A, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, gen:mc\|H, gen:mc\|V, gen:mc\|D, gen:mc\|A, test:nc\|Z, test:nc\|X, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|Z, test:H\|X, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|Z, test:V\|X, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|Z, test:D\|X, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|Z, test:A\|X, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|Z, test:mc\|X, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A |
| `raw_joint_distribution` | an object of 72 fields (9,927 characters); not shown, see the record |
| `refused` | false |
| `support` | gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A |
| `tail_evaluation` | sweep |

## <a id="p-.payload.stages.acceptance_construction.geometry"></a>/payload/stages/acceptance_construction/geometry

`PolytopeGeometry`

## <a id="p-.payload.stages.acceptance_construction.honest_distribution"></a>/payload/stages/acceptance_construction/honest_distribution

| Field | Value |
| --- | --- |
| `gen` | 4177591903144347932842466261189682624755296888382610605329/160213213824283484808215031606401923292237462789562505887744 |
| `gen:X\|A` | 0 |
| `gen:X\|D` | 0 |
| `gen:X\|H` | 0 |
| `gen:X\|V` | 0 |
| `gen:X\|Z` | 138115888362162844362357982798291520003969766092532920027/10923628215292055782378297609527403860834372462924716310528 |
| `gen:X\|mc` | 192533276869062680241968351361424157765677156953407/21847256430584111564756595219054807721668744925849432621056 |
| `gen:X\|nc` | 16975570586625353710271420823185061765057761763481169074297/240319820736425227212322547409602884938356194184343758831616 |
| `gen:Z\|A` | 0 |
| `gen:Z\|D` | 0 |
| `gen:Z\|H` | 0 |
| `gen:Z\|V` | 0 |
| `gen:Z\|X` | 253152424742436476671043867512857378804340447752527703065/20026651728035435601026878950800240411529682848695313235968 |
| `gen:Z\|mc` | 1198137209222655507888063470561528271767713685447713/106808809216188989872143354404267948861491641859708337258496 |
| `gen:Z\|nc` | 86417525643720164571999943054032582168049841666541088216001/961279282945700908849290189638411539753424776737375035326464 |
| `gen:mc\|A` | 0 |
| `gen:mc\|D` | 0 |
| `gen:mc\|H` | 0 |
| `gen:mc\|V` | 0 |
| `gen:mc\|X` | 529396289322552459872704280183981757947152761068581/60079955184106306803080636852400721234589048546085939707904 |
| `gen:mc\|Z` | 5392179301046868116804325235486565808212968240515643/480639641472850454424645094819205769876712388368687517663232 |
| `gen:mc\|mc` | 834369577746549002129601646932087513940580765/106808809216188989872143354404267948861491641859708337258496 |
| `gen:mc\|nc` | 6687185869194771836354286560562459812087300115660877/106808809216188989872143354404267948861491641859708337258496 |
| `gen:nc\|A` | 0 |
| `gen:nc\|D` | 0 |
| `gen:nc\|H` | 0 |
| `gen:nc\|V` | 0 |
| `gen:nc\|X` | 3274747498835761349473459337466807658030809197207608621/46357990111193137965339997571296852804466858446053965824 |
| `gen:nc\|Z` | 21603660963615202092523505650098285498318169056259210484599/240319820736425227212322547409602884938356194184343758831616 |
| `gen:nc\|mc` | 30092336494382432308560659652011280332383431812048575/480639641472850454424645094819205769876712388368687517663232 |
| `gen:nc\|nc` | 26839362874212365221937291778261796355638794412669712409595/53404404608094494936071677202133974430745820929854168629248 |
| `test:A\|A` | 102319179364102270047125849202943993221012975416210914675/160213213824283484808215031606401923292237462789562505887744 |
| `test:A\|D` | 8351821404130750429645970255491477081618679678565072215/480639641472850454424645094819205769876712388368687517663232 |
| `test:A\|H` | 54192347500519460360501472245827229169373393825054268579/120159910368212613606161273704801442469178097092171879415808 |
| `test:A\|V` | 101001372918013334631744805380973159501583135989516924513/240319820736425227212322547409602884938356194184343758831616 |
| `test:A\|X` | 0 |
| `test:A\|Z` | 0 |
| `test:A\|mc` | 286291609624970579269943020323391876496612719267361/480639641472850454424645094819205769876712388368687517663232 |
| `test:A\|nc` | 2353907934475087023483788028005577643052151789934771526881/480639641472850454424645094819205769876712388368687517663232 |
| `test:D\|A` | 8351820798371410806801997005033076738844903706952250305/480639641472850454424645094819205769876712388368687517663232 |
| `test:D\|D` | 359733384987427401317053153028818778974482370507424417935/480639641472850454424645094819205769876712388368687517663232 |
| `test:D\|H` | 58153872605992985762788502201794492889375132309808841079/120159910368212613606161273704801442469178097092171879415808 |
| `test:D\|V` | 108384693150044998260514620232699602107681933745860319113/240319820736425227212322547409602884938356194184343758831616 |
| `test:D\|X` | 0 |
| `test:D\|Z` | 0 |
| `test:D\|mc` | 106270991606884995734938218461313730255648019909687/160213213824283484808215031606401923292237462789562505887744 |
| `test:D\|nc` | 2496255090275014036593760778618725718392922999631276780061/480639641472850454424645094819205769876712388368687517663232 |
| `test:H\|A` | 27000212241512202601976947151681501224771733296789601441/53404404608094494936071677202133974430745820929854168629248 |
| `test:H\|D` | 7553853105894127993939595559033162815597320572024574277/17801468202698164978690559067377991476915273643284722876416 |
| `test:H\|H` | 16250558607963321172168056897140082446264590003512884009/13351101152023623734017919300533493607686455232463542157312 |
| `test:H\|V` | 634030324141629692816326811392303511246633500070781163/26702202304047247468035838601066987215372910464927084314624 |
| `test:H\|X` | 0 |
| `test:H\|Z` | 0 |
| `test:H\|mc` | 5023719612064897015114044552611894037284048226155/5933822734232721659563519689125997158971757881094907625472 |
| `test:H\|nc` | 39186150451140284699853407049870437589848396736810928763/5933822734232721659563519689125997158971757881094907625472 |
| `test:V\|A` | 355986640080750958151607158293531697422070449232464259539/961279282945700908849290189638411539753424776737375035326464 |
| `test:V\|D` | 486003812944739466227227581448003943148117539410471581725/961279282945700908849290189638411539753424776737375035326464 |
| `test:V\|H` | 1902090871902940446023276057690824076055868731073803089/80106606912141742404107515803200961646118731394781252943872 |
| `test:V\|V` | 499156763684123344892723285363439293855699645079649356869/480639641472850454424645094819205769876712388368687517663232 |
| `test:V\|X` | 0 |
| `test:V\|Z` | 0 |
| `test:V\|mc` | 80735505443211211997670550990347089009989086993169/106808809216188989872143354404267948861491641859708337258496 |
| `test:V\|nc` | 5997204433161011674623739922782786563023108538142499285537/961279282945700908849290189638411539753424776737375035326464 |
| `test:mc\|A` | 574316701140330889152716145586153775378176752428485/961279282945700908849290189638411539753424776737375035326464 |
| `test:mc\|D` | 19264604853586680233308465211431306058472757186571/29129675240778815419675460292073076962224993234465910161408 |
| `test:mc\|H` | 203934211616004570122869624459733035497840347218681/240319820736425227212322547409602884938356194184343758831616 |
| `test:mc\|V` | 32949355044452001754339616792861081964197446486417/43694512861168223129513190438109615443337489851698865242112 |
| `test:mc\|X` | 0 |
| `test:mc\|Z` | 0 |
| `test:mc\|mc` | 119195653963792714589943092418869644848654395/106808809216188989872143354404267948861491641859708337258496 |
| `test:mc\|nc` | 955312267027824548050612365794637116012471445094411/106808809216188989872143354404267948861491641859708337258496 |
| `test:nc\|A` | 2351684839831243032437370447640604069489378896491880286833/480639641472850454424645094819205769876712388368687517663232 |
| `test:nc\|D` | 2498684027015781777754176182481661901719682497315046310671/480639641472850454424645094819205769876712388368687517663232 |
| `test:nc\|H` | 264304104151585398321982597444399548730389875088463735381/40053303456070871202053757901600480823059365697390626471936 |
| `test:nc\|V` | 1500412655606945051857176651061929207377399186077676228371/240319820736425227212322547409602884938356194184343758831616 |
| `test:nc\|X` | 0 |
| `test:nc\|Z` | 0 |
| `test:nc\|mc` | 4298905213483204615508665664573040047483347401721225/480639641472850454424645094819205769876712388368687517663232 |
| `test:nc\|nc` | 3834194696316052174562470254037399479376970630381387487085/53404404608094494936071677202133974430745820929854168629248 |

## <a id="p-.payload.stages.acceptance_construction.outcomes"></a>/payload/stages/acceptance_construction/outcomes

gen, gen:Z\|X, gen:Z\|nc, gen:Z\|mc, gen:Z\|H, gen:Z\|V, gen:Z\|D, gen:Z\|A, gen:X\|Z, gen:X\|nc, gen:X\|mc, gen:X\|H, gen:X\|V, gen:X\|D, gen:X\|A, gen:nc\|Z, gen:nc\|X, gen:nc\|nc, gen:nc\|mc, gen:nc\|H, gen:nc\|V, gen:nc\|D, gen:nc\|A, gen:mc\|Z, gen:mc\|X, gen:mc\|nc, gen:mc\|mc, gen:mc\|H, gen:mc\|V, gen:mc\|D, gen:mc\|A, test:nc\|Z, test:nc\|X, test:nc\|nc, test:nc\|mc, test:nc\|H, test:nc\|V, test:nc\|D, test:nc\|A, test:H\|Z, test:H\|X, test:H\|nc, test:H\|mc, test:H\|H, test:H\|V, test:H\|D, test:H\|A, test:V\|Z, test:V\|X, test:V\|nc, test:V\|mc, test:V\|H, test:V\|V, test:V\|D, test:V\|A, test:D\|Z, test:D\|X, test:D\|nc, test:D\|mc, test:D\|H, test:D\|V, test:D\|D, test:D\|A, test:A\|Z, test:A\|X, test:A\|nc, test:A\|mc, test:A\|H, test:A\|V, test:A\|D, test:A\|A, test:mc\|Z, test:mc\|X, test:mc\|nc, test:mc\|mc, test:mc\|H, test:mc\|V, test:mc\|D, test:mc\|A

## <a id="p-.payload.stages.acceptance_construction.raw_joint_distribution"></a>/payload/stages/acceptance_construction/raw_joint_distribution

| Field | Value |
| --- | --- |
| `x0\|(A,gen)__A` | 716234255548715890329880944420607952547090827913476402725/160213213824283484808215031606401923292237462789562505887744 |
| `x0\|(A,gen)__D` | 58462749828915253007521791788440339571330757749955505505/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(A,gen)__H` | 379346432503636222523510305720790604185613756775379880053/120159910368212613606161273704801442469178097092171879415808 |
| `x0\|(A,gen)__V` | 707009610426093342422213637666812116511081951926618471591/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(A,gen)__mc` | 2004041267374794054889601142263743135476289034871527/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(A,gen)__nc` | 16477355541325609164386516196039043501365062529543400688167/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(A,test)__A` | 102319179364102270047125849202943993221012975416210914675/160213213824283484808215031606401923292237462789562505887744 |
| `x0\|(A,test)__D` | 8351821404130750429645970255491477081618679678565072215/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(A,test)__H` | 54192347500519460360501472245827229169373393825054268579/120159910368212613606161273704801442469178097092171879415808 |
| `x0\|(A,test)__V` | 101001372918013334631744805380973159501583135989516924513/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(A,test)__mc` | 286291609624970579269943020323391876496612719267361/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(A,test)__nc` | 2353907934475087023483788028005577643052151789934771526881/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,gen)__A` | 58462745588599875647613979035231537171914325948665752135/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,gen)__D` | 2518133694911991809219372071201731452821376593551970925545/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,gen)__H` | 407077108241950900339519515412561450225625926168661887553/120159910368212613606161273704801442469178097092171879415808 |
| `x0\|(D,gen)__V` | 758692852050314987823602341628897214753773536221022233791/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(D,gen)__mc` | 743896941248194970144567529229196111789536139367809/160213213824283484808215031606401923292237462789562505887744 |
| `x0\|(D,gen)__nc` | 17473785631925098256156325450331080028750460997418937460427/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,test)__A` | 8351820798371410806801997005033076738844903706952250305/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,test)__D` | 359733384987427401317053153028818778974482370507424417935/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(D,test)__H` | 58153872605992985762788502201794492889375132309808841079/120159910368212613606161273704801442469178097092171879415808 |
| `x0\|(D,test)__V` | 108384693150044998260514620232699602107681933745860319113/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(D,test)__mc` | 106270991606884995734938218461313730255648019909687/160213213824283484808215031606401923292237462789562505887744 |
| `x0\|(D,test)__nc` | 2496255090275014036593760778618725718392922999631276780061/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(H,gen)__A` | 189001485690585418213838630061770508573402133077527210087/53404404608094494936071677202133974430745820929854168629248 |
| `x0\|(H,gen)__D` | 52876971741258895957577168913232139709181244004172019939/17801468202698164978690559067377991476915273643284722876416 |
| `x0\|(H,gen)__H` | 113753910255743248205176398279980577123852130024590188063/13351101152023623734017919300533493607686455232463542157312 |
| `x0\|(H,gen)__V` | 4438212268991407849714287679746124578726434500495468141/26702202304047247468035838601066987215372910464927084314624 |
| `x0\|(H,gen)__mc` | 35166037284454279105798311868283258260988337583085/5933822734232721659563519689125997158971757881094907625472 |
| `x0\|(H,gen)__nc` | 274303053157981992898973849349093063128938777157676501341/5933822734232721659563519689125997158971757881094907625472 |
| `x0\|(H,test)__A` | 27000212241512202601976947151681501224771733296789601441/53404404608094494936071677202133974430745820929854168629248 |
| `x0\|(H,test)__D` | 7553853105894127993939595559033162815597320572024574277/17801468202698164978690559067377991476915273643284722876416 |
| `x0\|(H,test)__H` | 16250558607963321172168056897140082446264590003512884009/13351101152023623734017919300533493607686455232463542157312 |
| `x0\|(H,test)__V` | 634030324141629692816326811392303511246633500070781163/26702202304047247468035838601066987215372910464927084314624 |
| `x0\|(H,test)__mc` | 5023719612064897015114044552611894037284048226155/5933822734232721659563519689125997158971757881094907625472 |
| `x0\|(H,test)__nc` | 39186150451140284699853407049870437589848396736810928763/5933822734232721659563519689125997158971757881094907625472 |
| `x0\|(V,gen)__A` | 2491906480565256707061250108054721881954493144627249816773/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(V,gen)__D` | 3402026690613176263590593070136027602036822775873301072075/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(V,gen)__H` | 13314636103320583122162932403835768532391081117516621623/80106606912141742404107515803200961646118731394781252943872 |
| `x0\|(V,gen)__V` | 3494097345788863414249062997544075056989897515557545498083/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(V,gen)__mc` | 565148538102478483983693856932429623069923608952183/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(V,gen)__nc` | 41980431032127081722366179459479505941161759766997494998759/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(V,test)__A` | 355986640080750958151607158293531697422070449232464259539/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(V,test)__D` | 486003812944739466227227581448003943148117539410471581725/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(V,test)__H` | 1902090871902940446023276057690824076055868731073803089/80106606912141742404107515803200961646118731394781252943872 |
| `x0\|(V,test)__V` | 499156763684123344892723285363439293855699645079649356869/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(V,test)__mc` | 80735505443211211997670550990347089009989086993169/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(V,test)__nc` | 5997204433161011674623739922782786563023108538142499285537/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(mc,gen)__A` | 4020216907982316224069013019103076427647237266999395/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(mc,gen)__D` | 134852233975106761633159256480019142409309300305997/29129675240778815419675460292073076962224993234465910161408 |
| `x0\|(mc,gen)__H` | 1427539481312031990860087371218131248484882430530767/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(mc,gen)__V` | 230645485311164012280377317550027573749382125404919/43694512861168223129513190438109615443337489851698865242112 |
| `x0\|(mc,gen)__mc` | 834369577746549002129601646932087513940580765/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(mc,gen)__nc` | 6687185869194771836354286560562459812087300115660877/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(mc,test)__A` | 574316701140330889152716145586153775378176752428485/961279282945700908849290189638411539753424776737375035326464 |
| `x0\|(mc,test)__D` | 19264604853586680233308465211431306058472757186571/29129675240778815419675460292073076962224993234465910161408 |
| `x0\|(mc,test)__H` | 203934211616004570122869624459733035497840347218681/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(mc,test)__V` | 32949355044452001754339616792861081964197446486417/43694512861168223129513190438109615443337489851698865242112 |
| `x0\|(mc,test)__mc` | 119195653963792714589943092418869644848654395/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(mc,test)__nc` | 955312267027824548050612365794637116012471445094411/106808809216188989872143354404267948861491641859708337258496 |
| `x0\|(nc,gen)__A` | 16461793878818701227061593133484228486425652275443162007831/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,gen)__D` | 17490788189110472444279233277371633312037777481205324174697/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,gen)__H` | 1850128729061097788253878182110796841112729125619246147667/40053303456070871202053757901600480823059365697390626471936 |
| `x0\|(nc,gen)__V` | 10502888589248615363000236557433504451641794302543733598597/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(nc,gen)__mc` | 30092336494382432308560659652011280332383431812048575/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,gen)__nc` | 26839362874212365221937291778261796355638794412669712409595/53404404608094494936071677202133974430745820929854168629248 |
| `x0\|(nc,test)__A` | 2351684839831243032437370447640604069489378896491880286833/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,test)__D` | 2498684027015781777754176182481661901719682497315046310671/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,test)__H` | 264304104151585398321982597444399548730389875088463735381/40053303456070871202053757901600480823059365697390626471936 |
| `x0\|(nc,test)__V` | 1500412655606945051857176651061929207377399186077676228371/240319820736425227212322547409602884938356194184343758831616 |
| `x0\|(nc,test)__mc` | 4298905213483204615508665664573040047483347401721225/480639641472850454424645094819205769876712388368687517663232 |
| `x0\|(nc,test)__nc` | 3834194696316052174562470254037399479376970630381387487085/53404404608094494936071677202133974430745820929854168629248 |

## <a id="p-.payload.stages.compilation"></a>/payload/stages/compilation

| Field | Value |
| --- | --- |
| `refused` | false |

## <a id="p-.payload.stages.key_rate"></a>/payload/stages/key_rate

| Field | Value |
| --- | --- |
| `accumulation_rule` | maximum over the CONTRIBUTING iterates of the first-order linearization O^J_alpha(x_t) + &lt;g_t, v_t - q_t> + b^F_t - &lt;G_t, J_t> of Eq. eq:hlb with the lower bounds of Theorem thm:firstorder (iv): v_t the exact acceptance-side minimiser and b^F_t the feasible-side bound of Lemma lem:feasible-side-dual, verified exactly from the oracle's dual (req:verified-feasible-side) and rounded toward -inf, over every iterate the loop formed at which (H-POS), (H-SUPP) and (H-NOPERT) held and the point was established to lie in AcceptSet x Feas^J(epsilon). Under those hypotheses each bracket is a lower bound on h_low IN EXACT REAL ARITHMETIC (Theorem thm:firstorder (iiib), (iv)), and the maximum of lower bounds is a lower bound. An iterate failing any of them CONTRIBUTES NO BRACKET; the oracle's return and status withdraw none |
| `alpha` | 1.00435275282 |
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
| `block_contributions/gen/('A', 'C_0__C_0')` | -1.9783655955046279e-16 |
| `block_contributions/gen/('A', 'C_0__C_1')` | -1.229939290931699e-10 |
| `block_contributions/gen/('A', 'C_0__C_A')` | -1.1925477278609938e-17 |
| `block_contributions/gen/('A', 'C_0__C_D')` | -1.1468900408467806e-17 |
| `block_contributions/gen/('A', 'C_0__C_H')` | -1.1483486331124784e-17 |
| `block_contributions/gen/('A', 'C_0__C_V')` | -1.202516353261104e-17 |
| `block_contributions/gen/('A', 'C_1__C_0')` | -5.56181454741645e-12 |
| `block_contributions/gen/('A', 'C_1__C_1')` | -6.462877027246447e-05 |
| `block_contributions/gen/('A', 'C_1__C_A')` | -5.283987029468561e-17 |
| `block_contributions/gen/('A', 'C_1__C_D')` | -6.3010460848252e-17 |
| `block_contributions/gen/('A', 'C_1__C_H')` | -1.1789388635728213e-14 |
| `block_contributions/gen/('A', 'C_1__C_V')` | -4.592575543760199e-11 |
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
| `certified/certified_bound` | 0.021811680981575748 |
| `certified/certified_evaluation` | on |
| `certified/certified_minus_first_order` | -9.208445813849741e-14 |
| `certified/declaration` | reference_companion |
| `certified/first_order_key_length` | 289368 |
| `certified/max_gradient_radius` | 7.49537715244762e-29 |
| `certified/points/0/acceptance_side_bound` | 332.9087908427961 |
| `certified/points/0/certified` | true |
| `certified/points/0/certified_bracket` | 0.021811680981575748 |
| `certified/points/0/detail` | \[\] |
| `certified/points/0/feasible_side_bound` | -332.88697916181457 |
| `certified/points/0/gradient_radius` | 7.32250432646993e-29 |
| `certified/points/0/index` | 0 |
| `certified/points/0/iteration` | 2 |
| `certified/points/0/reasons` | \[\] |
| `certified/points/0/sequence` | 37 |
| `certified/points/0/set` | polish |
| `certified/points/1/acceptance_side_bound` | 332.9087908426325 |
| `certified/points/1/certified` | true |
| `certified/points/1/certified_bracket` | 0.02181167979006421 |
| `certified/points/1/detail` | \[\] |
| `certified/points/1/feasible_side_bound` | -332.8869791628425 |
| `certified/points/1/gradient_radius` | 7.32250432646993e-29 |
| `certified/points/1/index` | 1 |
| `certified/points/1/iteration` | 24 |
| `certified/points/1/reasons` | \[\] |
| `certified/points/1/sequence` | 24 |
| `certified/points/1/set` | search |
| `certified/points/2/acceptance_side_bound` | 332.90879084263577 |
| `certified/points/2/certified` | true |
| `certified/points/2/certified_bracket` | 0.02181161161757401 |
| `certified/points/2/detail` | \[\] |
| `certified/points/2/feasible_side_bound` | -332.88697923101824 |
| `certified/points/2/gradient_radius` | 7.49537715244762e-29 |
| `certified/points/2/index` | 2 |
| `certified/points/2/iteration` | 23 |
| `certified/points/2/reasons` | \[\] |
| `certified/points/2/sequence` | 23 |
| `certified/points/2/set` | search |
| `certified/points/3/acceptance_side_bound` | 332.90879084262326 |
| `certified/points/3/certified` | true |
| `certified/points/3/certified_bracket` | 0.021811127723474766 |
| `certified/points/3/detail` | \[\] |
| `certified/points/3/feasible_side_bound` | -332.88697971489984 |
| `certified/points/3/gradient_radius` | 5.432646297624682e-29 |
| `certified/points/3/index` | 3 |
| `certified/points/3/iteration` | 32 |
| `certified/points/3/reasons` | \[\] |
| `certified/points/3/sequence` | 32 |
| `certified/points/3/set` | search |
| `certified/premises` | \[\] |
| `certified/reasons` | \[\] |
| `certified/resting_blocks` | \[\] |
| `certified/seconds` | 0.1975778000196442 |
| `certified/status` | certified |
| `certified/working_precision_bits` | 128 |
| `claim_roots` | meat-core/frank-wolfe/cor:fo-reference, meat-core/frank-wolfe/cor:certified-keylength, meat-core/frank-wolfe/cor:certified-keylength-reference, meat-core/cor:keylength-bound |
| `constraint_entries_through_a_reductions_chain` | 0 |
| `deductions/accepted_state_flag_bonus` | 1.0 |
| `deductions/error_correction_lambda_ec` | 74479.0 |
| `deductions/error_verification` | 30.0 |
| `deductions/privacy_amplification` | 6922.190124409548 |
| `deductions/two_universal_hash_penalty` | 0.0 |
| `dropped_set` | \[\] |
| `estimate_point_relaxed_member` | true |
| `first_order_clamped` | false |
| `first_order_minus_estimate` | -3.425740774977426e-07 |
| `frank_wolfe_gap` | 3.8467176339190357e-07 |
| `group_b_worst/constraint_rows/consumed_point/at` | — |
| `group_b_worst/constraint_rows/consumed_point/iteration` | 1 |
| `group_b_worst/constraint_rows/consumed_point/worst` | 0.0 |
| `group_b_worst/constraint_rows/declared` | 1e-07 |
| `group_b_worst/constraint_rows/kind` | spectral_floor |
| `group_b_worst/constraint_rows/returned_point/at` | — |
| `group_b_worst/constraint_rows/returned_point/iteration` | — |
| `group_b_worst/constraint_rows/returned_point/worst` | 0.0 |
| `group_b_worst/iterate_coupling/consumed_point/at` | \* |
| `group_b_worst/iterate_coupling/consumed_point/iteration` | 6 |
| `group_b_worst/iterate_coupling/consumed_point/worst` | 2.220446049250313e-16 |
| `group_b_worst/iterate_coupling/declared` | 1e-07 |
| `group_b_worst/iterate_coupling/kind` | entrywise |
| `group_b_worst/iterate_coupling/returned_point/at` | \* |
| `group_b_worst/iterate_coupling/returned_point/iteration` | — |
| `group_b_worst/iterate_coupling/returned_point/worst` | 0.0 |
| `group_b_worst/iterate_positivity/at` | A\_\_C_1\_\_C_D |
| `group_b_worst/iterate_positivity/declared` | 0.0 |
| `group_b_worst/iterate_positivity/iteration` | 24 |
| `group_b_worst/iterate_positivity/kind` | spectral_floor |
| `group_b_worst/iterate_positivity/returned_point/at` | A\_\_C_1\_\_C_D |
| `group_b_worst/iterate_positivity/returned_point/iteration` | — |
| `group_b_worst/iterate_positivity/returned_point/worst` | 7.819249981720004e-13 |
| `group_b_worst/iterate_positivity/worst` | 7.812501204180901e-13 |
| `group_b_worst/iterate_repair_window/at` | — |
| `group_b_worst/iterate_repair_window/declared` | 1e-07 |
| `group_b_worst/iterate_repair_window/iteration` | — |
| `group_b_worst/iterate_repair_window/kind` | spectral_floor |
| `group_b_worst/iterate_repair_window/note` | this driver takes the REJECT branch of rem:fo-iterate-repair and repairs no formed iterate, so nothing was compared against the window as a repair |
| `group_b_worst/iterate_repair_window/worst` | — |
| `group_b_worst/optimizer_gap/at` | — |
| `group_b_worst/optimizer_gap/declared` | 1e-10 |
| `group_b_worst/optimizer_gap/iteration` | 35 |
| `group_b_worst/optimizer_gap/kind` | not_a_predicate |
| `group_b_worst/optimizer_gap/worst` | 3.8467176339190357e-07 |
| `group_b_worst/oracle_repair_window/at/block` | A\_\_C_A\_\_C_D |
| `group_b_worst/oracle_repair_window/at/group` | \* |
| `group_b_worst/oracle_repair_window/declared` | 1e-07 |
| `group_b_worst/oracle_repair_window/iteration` | 30 |
| `group_b_worst/oracle_repair_window/kind` | spectral_floor |
| `group_b_worst/oracle_repair_window/repairs` | 800 |
| `group_b_worst/oracle_repair_window/worst` | -7.540702310067862e-11 |
| `h_lb` | 0.021811680981667834 |
| `h_low` | 0.02181202355574533 |
| `h_low_is_infinite` | false |
| `iterations` | 35 |
| `joint_solver/assignment/*` | qics |
| `joint_solver/oracle` | qics |
| `joint_solver/search` | auto |
| `joint_solver/warm_start` | — |
| `key_length` | 289368 |
| `key_length_reason` | certified_reported: the bracket was formed again at the run's final points from the declaration's data with every arithmetic step exact or rigorously enclosed (frank-wolfe/req:certified-evaluation), and the key length is computed exactly from max{0, h_cert} by frank-wolfe/cor:certified-keylength; the first-order number and its key length are recorded beside it |
| `key_length_reason_code` | certified_reported |
| `map_validation_report/alice_sectors` | A |
| `map_validation_report/declaration_admitted_exactly` | true |
| `map_validation_report/factor_labels` | alice_station, bob_station |
| `map_validation_report/hsupp_reference_band/factor_support_cutoff` | 1e-06 |
| `map_validation_report/hsupp_reference_band/note` | per key-active pair, the directions of ran K whose singular value lies in (support_cutoff, sqrt(support_cutoff)\] relative to the largest: not counted in dim W under rem:fo-one-ruler, and no rank of X counts them either. Diagnostic only; decides nothing |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_0')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_A')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_D')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_H')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_0__C_V')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_0')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_1')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_A')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_D')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_H')` | 0 |
| `map_validation_report/hsupp_reference_band/pairs/gen/('A', 'C_1__C_V')` | 0 |
| `map_validation_report/hsupp_reference_band/relative_to` | the largest singular value of the pair's Kraus stack |
| `map_validation_report/hsupp_reference_band/support_cutoff` | 1e-12 |
| `mathematical_spec_version` | meat-core@1.28.0 |
| `module_versions/meat-core` | 1.32.0 |
| `module_versions/meat-core/frank-wolfe` | 0.19.0 |
| `net_key_length` | 289368 |
| `optimized_q/gen` | 0.025837294117647056 |
| `optimized_q/gen_X_A` | 0.0 |
| `optimized_q/gen_X_D` | 0.0 |
| `optimized_q/gen_X_H` | 0.0 |
| `optimized_q/gen_X_V` | 0.0 |
| `optimized_q/gen_X_Z` | 0.01251951350488573 |
| `optimized_q/gen_X_mc` | 8.235294117647059e-07 |
| `optimized_q/gen_X_nc` | 0.0708484820474111 |
| `optimized_q/gen_Z_A` | 0.0 |
| `optimized_q/gen_Z_D` | 0.0 |
| `optimized_q/gen_Z_H` | 0.0 |
| `optimized_q/gen_Z_V` | 0.0 |
| `optimized_q/gen_Z_X` | 0.012519316748974963 |
| `optimized_q/gen_Z_mc` | 8.235294117647059e-07 |
| `optimized_q/gen_Z_nc` | 0.09019096732557388 |
| `optimized_q/gen_mc_A` | 0.0 |
| `optimized_q/gen_mc_D` | 0.0 |
| `optimized_q/gen_mc_H` | 0.0 |
| `optimized_q/gen_mc_V` | 0.0 |
| `optimized_q/gen_mc_X` | 8.235294117647059e-07 |
| `optimized_q/gen_mc_Z` | 8.235294117647059e-07 |
| `optimized_q/gen_mc_mc` | 1.599713107967077e-07 |
| `optimized_q/gen_mc_nc` | 8.885534574417422e-07 |
| `optimized_q/gen_nc_A` | 0.0 |
| `optimized_q/gen_nc_D` | 0.0 |
| `optimized_q/gen_nc_H` | 0.0 |
| `optimized_q/gen_nc_V` | 0.0 |
| `optimized_q/gen_nc_X` | 0.07030259669754102 |
| `optimized_q/gen_nc_Z` | 0.08947495819047471 |
| `optimized_q/gen_nc_mc` | 8.586859797778994e-07 |
| `optimized_q/gen_nc_nc` | 0.503313869815746 |
| `optimized_q/test_A_A` | 0.0006229483522993644 |
| `optimized_q/test_A_D` | 2.4e-05 |
| `optimized_q/test_A_H` | 0.0004795855244370237 |
| `optimized_q/test_A_V` | 0.00038935294117647056 |
| `optimized_q/test_A_X` | 0.0 |
| `optimized_q/test_A_Z` | 0.0 |
| `optimized_q/test_A_mc` | 5.460537082655716e-08 |
| `optimized_q/test_A_nc` | 0.0049170418708067536 |
| `optimized_q/test_D_A` | 2.4e-05 |
| `optimized_q/test_D_D` | 0.0007263356382619073 |
| `optimized_q/test_D_H` | 0.00045405786826866623 |
| `optimized_q/test_D_V` | 0.0004672764112930022 |
| `optimized_q/test_D_X` | 0.0 |
| `optimized_q/test_D_Z` | 0.0 |
| `optimized_q/test_D_mc` | 6.314292027121438e-08 |
| `optimized_q/test_D_nc` | 0.005204169850251978 |
| `optimized_q/test_H_A` | 0.00048323458974097863 |
| `optimized_q/test_H_D` | 0.0004500516371843397 |
| `optimized_q/test_H_H` | 0.0012077339550276415 |
| `optimized_q/test_H_V` | 3.141176470588236e-05 |
| `optimized_q/test_H_X` | 0.0 |
| `optimized_q/test_H_Z` | 0.0 |
| `optimized_q/test_H_mc` | 9.860514651866503e-10 |
| `optimized_q/test_H_nc` | 0.0066572714570372485 |
| `optimized_q/test_V_A` | 0.00038421490721774913 |
| `optimized_q/test_V_D` | 0.00047170588235294114 |
| `optimized_q/test_V_H` | 3.141176470588236e-05 |
| `optimized_q/test_V_V` | 0.0010067527459652302 |
| `optimized_q/test_V_X` | 0.0 |
| `optimized_q/test_V_Z` | 0.0 |
| `optimized_q/test_V_mc` | 1.171326673253136e-07 |
| `optimized_q/test_V_nc` | 0.006227152446616165 |
| `optimized_q/test_mc_A` | 4.822285364114209e-08 |
| `optimized_q/test_mc_D` | 6.984389555289831e-08 |
| `optimized_q/test_mc_H` | 1.2778514887852622e-09 |
| `optimized_q/test_mc_V` | 1.1655946073781721e-07 |
| `optimized_q/test_mc_X` | 0.0 |
| `optimized_q/test_mc_Z` | 0.0 |
| `optimized_q/test_mc_mc` | 2.2853044399529652e-08 |
| `optimized_q/test_mc_nc` | 1.2693620820596335e-07 |
| `optimized_q/test_nc_A` | 0.004864576378731928 |
| `optimized_q/test_nc_D` | 0.005178651720916784 |
| `optimized_q/test_nc_H` | 0.006588966727225581 |
| `optimized_q/test_nc_V` | 0.006193170157127941 |
| `optimized_q/test_nc_X` | 0.0 |
| `optimized_q/test_nc_Z` | 0.0 |
| `optimized_q/test_nc_mc` | 1.2266942568255694e-07 |
| `optimized_q/test_nc_nc` | 0.07190198140224942 |
| `optimizer_certificate` | an object of 16 fields (300,612 characters); not shown, see the record |
| `oracle_diagnostics` | a list of 35 items (229,205 characters); not shown, see the record |
| `per_iterate` | a list of 35 items (20,788 characters); not shown, see the record |
| `predicted_statistics/gen` | 0.02582508781449527 |
| `predicted_statistics/gen_X_A` | 0.0 |
| `predicted_statistics/gen_X_D` | 0.0 |
| `predicted_statistics/gen_X_H` | 0.0 |
| `predicted_statistics/gen_X_V` | 0.0 |
| `predicted_statistics/gen_X_Z` | 0.01251951347903583 |
| `predicted_statistics/gen_X_mc` | 8.242380359825384e-07 |
| `predicted_statistics/gen_X_nc` | 0.07084848190112539 |
| `predicted_statistics/gen_Z_A` | 0.0 |
| `predicted_statistics/gen_Z_D` | 0.0 |
| `predicted_statistics/gen_Z_H` | 0.0 |
| `predicted_statistics/gen_Z_V` | 0.0 |
| `predicted_statistics/gen_Z_X` | 0.01251931672312547 |
| `predicted_statistics/gen_Z_mc` | 8.268310298262859e-07 |
| `predicted_statistics/gen_Z_nc` | 0.0901909671393504 |
| `predicted_statistics/gen_mc_A` | 0.0 |
| `predicted_statistics/gen_mc_D` | 0.0 |
| `predicted_statistics/gen_mc_H` | 0.0 |
| `predicted_statistics/gen_mc_V` | 0.0 |
| `predicted_statistics/gen_mc_X` | 8.264672426518176e-07 |
| `predicted_statistics/gen_mc_Z` | 8.248611838830679e-07 |
| `predicted_statistics/gen_mc_mc` | 1.5997131046640377e-07 |
| `predicted_statistics/gen_mc_nc` | 8.885534556070847e-07 |
| `predicted_statistics/gen_nc_A` | 0.0 |
| `predicted_statistics/gen_nc_D` | 0.0 |
| `predicted_statistics/gen_nc_H` | 0.0 |
| `predicted_statistics/gen_nc_V` | 0.0 |
| `predicted_statistics/gen_nc_X` | 0.07030259655238243 |
| `predicted_statistics/gen_nc_Z` | 0.08947495800572955 |
| `predicted_statistics/gen_nc_mc` | 8.586859780049103e-07 |
| `predicted_statistics/gen_nc_nc` | 0.5033138687765193 |
| `predicted_statistics/test_A_A` | 0.0006229483510131205 |
| `predicted_statistics/test_A_D` | 2.886686577845282e-05 |
| `predicted_statistics/test_A_H` | 0.0004795855234467897 |
| `predicted_statistics/test_A_V` | 0.00038758212447043074 |
| `predicted_statistics/test_A_X` | 0.0 |
| `predicted_statistics/test_A_Z` | 0.0 |
| `predicted_statistics/test_A_mc` | 5.460537071380964e-08 |
| `predicted_statistics/test_A_nc` | 0.0049170418606542 |
| `predicted_statistics/test_D_A` | 2.885147403081008e-05 |
| `predicted_statistics/test_D_D` | 0.0007263356367621912 |
| `predicted_statistics/test_D_H` | 0.0004540578673311417 |
| `predicted_statistics/test_D_V` | 0.0004672764103281848 |
| `predicted_statistics/test_D_X` | 0.0 |
| `predicted_statistics/test_D_Z` | 0.0 |
| `predicted_statistics/test_D_mc` | 6.314292014083872e-08 |
| `predicted_statistics/test_D_nc` | 0.005204169839506572 |
| `predicted_statistics/test_H_A` | 0.00048323458874321057 |
| `predicted_statistics/test_H_D` | 0.000450051636255087 |
| `predicted_statistics/test_H_H` | 0.0012077339525339485 |
| `predicted_statistics/test_H_V` | 3.389318621416086e-05 |
| `predicted_statistics/test_H_X` | 0.0 |
| `predicted_statistics/test_H_Z` | 0.0 |
| `predicted_statistics/test_H_mc` | 9.86051463150682e-10 |
| `predicted_statistics/test_H_nc` | 0.006657271443291523 |
| `predicted_statistics/test_V_A` | 0.000384214906424434 |
| `predicted_statistics/test_V_D` | 0.0004709726861666212 |
| `predicted_statistics/test_V_H` | 3.391604899440624e-05 |
| `predicted_statistics/test_V_V` | 0.0010067527438865193 |
| `predicted_statistics/test_V_X` | 0.0 |
| `predicted_statistics/test_V_Z` | 0.0 |
| `predicted_statistics/test_V_mc` | 1.1713266708346156e-07 |
| `predicted_statistics/test_V_nc` | 0.006227152433758537 |
| `predicted_statistics/test_mc_A` | 4.822285354157298e-08 |
| `predicted_statistics/test_mc_D` | 6.984389540868668e-08 |
| `predicted_statistics/test_mc_H` | 1.2778514861467924e-09 |
| `predicted_statistics/test_mc_V` | 1.1655946049714863e-07 |
| `predicted_statistics/test_mc_X` | 0.0 |
| `predicted_statistics/test_mc_Z` | 0.0 |
| `predicted_statistics/test_mc_mc` | 2.2853044352343396e-08 |

119 more fields are not shown; see the record.

## <a id="p-.payload.stages.key_rate.alpha"></a>/payload/stages/key_rate/alpha

`1.00435275282`

## <a id="p-.payload.stages.key_rate.certified.certified_bound"></a>/payload/stages/key_rate/certified/certified_bound

`0.021811680981575748`

## <a id="p-.payload.stages.key_rate.deductions"></a>/payload/stages/key_rate/deductions

| Field | Value |
| --- | --- |
| `accepted_state_flag_bonus` | 1.0 |
| `error_correction_lambda_ec` | 74479.0 |
| `error_verification` | 30.0 |
| `privacy_amplification` | 6922.190124409548 |
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

`-3.425740774977426e-07`

## <a id="p-.payload.stages.key_rate.frank_wolfe_gap"></a>/payload/stages/key_rate/frank_wolfe_gap

`3.8467176339190357e-07`

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
| `iterate_coupling/consumed_point/iteration` | 6 |
| `iterate_coupling/consumed_point/worst` | 2.220446049250313e-16 |
| `iterate_coupling/declared` | 1e-07 |
| `iterate_coupling/kind` | entrywise |
| `iterate_coupling/returned_point/at` | \* |
| `iterate_coupling/returned_point/iteration` | — |
| `iterate_coupling/returned_point/worst` | 0.0 |
| `iterate_positivity/at` | A\_\_C_1\_\_C_D |
| `iterate_positivity/declared` | 0.0 |
| `iterate_positivity/iteration` | 24 |
| `iterate_positivity/kind` | spectral_floor |
| `iterate_positivity/returned_point/at` | A\_\_C_1\_\_C_D |
| `iterate_positivity/returned_point/iteration` | — |
| `iterate_positivity/returned_point/worst` | 7.819249981720004e-13 |
| `iterate_positivity/worst` | 7.812501204180901e-13 |
| `iterate_repair_window/at` | — |
| `iterate_repair_window/declared` | 1e-07 |
| `iterate_repair_window/iteration` | — |
| `iterate_repair_window/kind` | spectral_floor |
| `iterate_repair_window/note` | this driver takes the REJECT branch of rem:fo-iterate-repair and repairs no formed iterate, so nothing was compared against the window as a repair |
| `iterate_repair_window/worst` | — |
| `optimizer_gap/at` | — |
| `optimizer_gap/declared` | 1e-10 |
| `optimizer_gap/iteration` | 35 |
| `optimizer_gap/kind` | not_a_predicate |
| `optimizer_gap/worst` | 3.8467176339190357e-07 |
| `oracle_repair_window/at/block` | A\_\_C_A\_\_C_D |
| `oracle_repair_window/at/group` | \* |
| `oracle_repair_window/declared` | 1e-07 |
| `oracle_repair_window/iteration` | 30 |
| `oracle_repair_window/kind` | spectral_floor |
| `oracle_repair_window/repairs` | 800 |
| `oracle_repair_window/worst` | -7.540702310067862e-11 |

## <a id="p-.payload.stages.key_rate.h_lb"></a>/payload/stages/key_rate/h_lb

`0.021811680981667834`

## <a id="p-.payload.stages.key_rate.h_low"></a>/payload/stages/key_rate/h_low

`0.02181202355574533`

## <a id="p-.payload.stages.key_rate.iterations"></a>/payload/stages/key_rate/iterations

`35`

## <a id="p-.payload.stages.key_rate.joint_solver"></a>/payload/stages/key_rate/joint_solver

| Field | Value |
| --- | --- |
| `assignment/*` | qics |
| `oracle` | qics |
| `search` | auto |
| `warm_start` | — |

## <a id="p-.payload.stages.key_rate.key_length"></a>/payload/stages/key_rate/key_length

`289368`

## <a id="p-.payload.stages.key_rate.per_iterate"></a>/payload/stages/key_rate/per_iterate

| Field | Value |
| --- | --- |
| `0/acceptance_iterate_exact` | true |
| `0/constraint_row_residual` | 0.0 |
| `0/coupling_residual` | 0.0 |
| `0/coupling_residual_at` | \* |
| `0/dual_gap` | -2.9112925403751433e-09 |
| `0/feasible_side_bound` | -4487.227711617223 |
| `0/feasible_side_multipliers/*` | zero |
| `0/frame_deduction` | 0.0 |
| `0/iteration` | 1 |
| `0/linearization` | -3585.566691937496 |
| `0/min_block_eigenvalue` | 0.00390625 |
| `0/min_block_eigenvalue_at` | A\_\_C_1\_\_C_1 |
| `0/objective` | 568.7740408605223 |
| `0/oracle_optimal` | true |
| `0/oracle_pairing` | -4487.227711620134 |
| `0/oracle_status` | optimal |
| `0/row_multiplier_norm` | 0.0 |
| `0/withdrawal` | — |
| `1/acceptance_iterate_exact` | true |
| `1/constraint_row_residual` | 0.0 |
| `1/coupling_residual` | 1.1102230246251565e-16 |
| `1/coupling_residual_at` | \* |
| `1/dual_gap` | -2.0852440389886064e-08 |
| `1/feasible_side_bound` | -333.97055231853847 |
| `1/feasible_side_multipliers/*` | zero |
| `1/frame_deduction` | 0.0 |
| `1/iteration` | 2 |
| `1/linearization` | -1.0616447249791294 |
| `1/min_block_eigenvalue` | 1.1503568224727295e-11 |
| `1/min_block_eigenvalue_at` | A\_\_C_nc\_\_C_1 |
| `1/objective` | 0.021928774352323554 |
| `1/oracle_optimal` | true |
| `1/oracle_pairing` | -333.9705523393909 |
| `1/oracle_status` | optimal |
| `1/row_multiplier_norm` | 0.0 |
| `1/withdrawal` | — |
| `2/acceptance_iterate_exact` | true |
| `2/constraint_row_residual` | 0.0 |
| `2/coupling_residual` | 0.0 |
| `2/coupling_residual_at` | \* |
| `2/dual_gap` | -1.3187104741518851e-09 |
| `2/feasible_side_bound` | -333.19557854637316 |
| `2/feasible_side_multipliers/*` | zero |
| `2/frame_deduction` | 0.0 |
| `2/iteration` | 3 |
| `2/linearization` | -0.2867868668504374 |
| `2/min_block_eigenvalue` | 2.5261154989165254e-12 |
| `2/min_block_eigenvalue_at` | A\_\_C_nc\_\_C_D |
| `2/objective` | 0.02181286031564539 |
| `2/oracle_optimal` | true |
| `2/oracle_pairing` | -333.19557854769187 |
| `2/oracle_status` | optimal |
| `2/row_multiplier_norm` | 0.0 |
| `2/withdrawal` | — |
| `3/acceptance_iterate_exact` | true |
| `3/constraint_row_residual` | 0.0 |
| `3/coupling_residual` | 0.0 |
| `3/coupling_residual_at` | \* |
| `3/dual_gap` | -5.111871814733604e-09 |
| `3/feasible_side_bound` | -332.9164704745607 |
| `3/feasible_side_multipliers/*` | zero |
| `3/frame_deduction` | 0.0 |
| `3/iteration` | 4 |
| `3/linearization` | -0.007679459776532786 |
| `3/min_block_eigenvalue` | 9.76705001899674e-13 |
| `3/min_block_eigenvalue_at` | A\_\_C_1\_\_C_mc |
| `3/objective` | 0.02181219557709528 |
| `3/oracle_optimal` | true |
| `3/oracle_pairing` | -332.91647047967257 |
| `3/oracle_status` | optimal |
| `3/row_multiplier_norm` | 0.0 |
| `3/withdrawal` | — |
| `4/acceptance_iterate_exact` | true |
| `4/constraint_row_residual` | 0.0 |
| `4/coupling_residual` | 0.0 |
| `4/coupling_residual_at` | \* |
| `4/dual_gap` | -9.220851235320884e-09 |
| `4/feasible_side_bound` | -332.8932102193922 |
| `4/feasible_side_multipliers/*` | zero |
| `4/frame_deduction` | 0.0 |
| `4/iteration` | 5 |
| `4/linearization` | 0.015580717057098552 |
| `4/min_block_eigenvalue` | 1.5810353065687986e-12 |
| `4/min_block_eigenvalue_at` | A\_\_C_nc\_\_C_A |
| `4/objective` | 0.02181211724226079 |
| `4/oracle_optimal` | true |
| `4/oracle_pairing` | -332.893210228613 |
| `4/oracle_status` | optimal |
| `4/row_multiplier_norm` | 0.0 |
| `4/withdrawal` | — |
| `5/acceptance_iterate_exact` | true |
| `5/constraint_row_residual` | 0.0 |
| `5/coupling_residual` | 2.220446049250313e-16 |
| `5/coupling_residual_at` | \* |
| `5/dual_gap` | -9.370359401160951e-08 |
| `5/feasible_side_bound` | -333.0078576839359 |
| `5/feasible_side_multipliers/*` | zero |
| `5/frame_deduction` | 0.0 |
| `5/iteration` | 6 |
| `5/linearization` | -0.09906679934793709 |
| `5/min_block_eigenvalue` | 1.5018980254258695e-12 |
| `5/min_block_eigenvalue_at` | A\_\_C_1\_\_C_A |
| `5/objective` | 0.021812065380930768 |
| `5/oracle_optimal` | true |
| `5/oracle_pairing` | -333.0078577776395 |
| `5/oracle_status` | optimal |
| `5/row_multiplier_norm` | 0.0 |
| `5/withdrawal` | — |
| `6/acceptance_iterate_exact` | true |
| `6/constraint_row_residual` | 0.0 |
| `6/coupling_residual` | 0.0 |
| `6/coupling_residual_at` | \* |
| `6/dual_gap` | -5.171600990001532e-09 |
| `6/feasible_side_bound` | -332.88957698902726 |
| `6/feasible_side_multipliers/*` | zero |
| `6/frame_deduction` | 0.0 |
| `6/iteration` | 7 |
| `6/linearization` | 0.01921387399168957 |
| `6/min_block_eigenvalue` | 1.236663835059515e-12 |
| `6/min_block_eigenvalue_at` | A\_\_C_nc\_\_C_1 |
| `6/objective` | 0.02181204381182958 |
| `6/oracle_optimal` | true |
| `6/oracle_pairing` | -332.8895769941988 |
| `6/oracle_status` | optimal |
| `6/row_multiplier_norm` | 0.0 |
| `6/withdrawal` | — |
| `7/acceptance_iterate_exact` | true |
| `7/constraint_row_residual` | 0.0 |
| `7/coupling_residual` | 0.0 |
| `7/coupling_residual_at` | \* |
| `7/dual_gap` | -3.284756855803714e-08 |
| `7/feasible_side_bound` | -333.0746372636992 |
| `7/feasible_side_multipliers/*` | zero |
| `7/frame_deduction` | 0.0 |
| `7/iteration` | 8 |
| `7/linearization` | -0.16584641552839566 |
| `7/min_block_eigenvalue` | 1.2872363920374274e-12 |
| `7/min_block_eigenvalue_at` | A\_\_C_1\_\_C_V |
| `7/objective` | 0.021812028963831893 |
| `7/oracle_optimal` | true |
| `7/oracle_pairing` | -333.0746372965467 |
| `7/oracle_status` | optimal |
| `7/row_multiplier_norm` | 0.0 |
| `7/withdrawal` | — |
| `8/acceptance_iterate_exact` | true |
| `8/constraint_row_residual` | 0.0 |
| `8/coupling_residual` | 0.0 |
| `8/coupling_residual_at` | \* |
| `8/dual_gap` | -5.4257507558661424e-09 |
| `8/feasible_side_bound` | -332.8870084789374 |
| `8/feasible_side_multipliers/*` | zero |
| `8/frame_deduction` | 0.0 |
| `8/iteration` | 9 |
| `8/linearization` | 0.02178236584878606 |
| `8/min_block_eigenvalue` | 7.859609853798535e-13 |
| `8/min_block_eigenvalue_at` | A\_\_C_D\_\_C_1 |
| `8/objective` | 0.02181202557915545 |
| `8/oracle_optimal` | true |
| `8/oracle_pairing` | -332.8870084843631 |
| `8/oracle_status` | optimal |
| `8/row_multiplier_norm` | 0.0 |
| `8/withdrawal` | — |
| `9/acceptance_iterate_exact` | true |
| `9/constraint_row_residual` | 0.0 |
| `9/coupling_residual` | 1.1102230246251565e-16 |
| `9/coupling_residual_at` | \* |
| `9/dual_gap` | -5.301982385396583e-09 |
| `9/feasible_side_bound` | -332.8888373276593 |
| `9/feasible_side_multipliers/*` | zero |
| `9/frame_deduction` | 0.0 |
| `9/iteration` | 10 |
| `9/linearization` | 0.019953516042351693 |
| `9/min_block_eigenvalue` | 7.916573975467047e-13 |
| `9/min_block_eigenvalue_at` | A\_\_C_mc\_\_C_1 |
| `9/objective` | 0.02181202449467773 |
| `9/oracle_optimal` | true |
| `9/oracle_pairing` | -332.88883733296126 |
| `9/oracle_status` | optimal |
| `9/row_multiplier_norm` | 0.0 |
| `9/withdrawal` | — |
| `10/acceptance_iterate_exact` | true |
| `10/constraint_row_residual` | 0.0 |
| `10/coupling_residual` | 2.220446049250313e-16 |
| `10/coupling_residual_at` | \* |
| `10/dual_gap` | -1.0905679132110832e-07 |
| `10/feasible_side_bound` | -332.8871214973919 |
| `10/feasible_side_multipliers/*` | zero |
| `10/frame_deduction` | 0.0 |
| `10/iteration` | 11 |
| `10/linearization` | 0.02166934588598555 |
| `10/min_block_eigenvalue` | 7.813396447742059e-13 |
| `10/min_block_eigenvalue_at` | A\_\_C_mc\_\_C_1 |
| `10/objective` | 0.021812024070858634 |
| `10/oracle_optimal` | true |
| `10/oracle_pairing` | -332.88712160644866 |
| `10/oracle_status` | optimal |
| `10/row_multiplier_norm` | 0.0 |
| `10/withdrawal` | — |
| `11/acceptance_iterate_exact` | true |
| `11/constraint_row_residual` | 0.0 |
| `11/coupling_residual` | 0.0 |
| `11/coupling_residual_at` | \* |
| `11/dual_gap` | -7.699637070291477e-09 |
| `11/feasible_side_bound` | -332.88701385644526 |
| `11/feasible_side_multipliers/*` | zero |
| `11/frame_deduction` | 0.0 |
| `11/iteration` | 12 |
| `11/linearization` | 0.021776986726939927 |
| `11/min_block_eigenvalue` | 7.829643958783639e-13 |
| `11/min_block_eigenvalue_at` | A\_\_C_1\_\_C_A |
| `11/objective` | 0.021812023965283246 |
| `11/oracle_optimal` | true |
| `11/oracle_pairing` | -332.8870138641449 |
| `11/oracle_status` | optimal |
| `11/row_multiplier_norm` | 0.0 |
| `11/withdrawal` | — |
| `12/acceptance_iterate_exact` | true |
| `12/constraint_row_residual` | 0.0 |
| `12/coupling_residual` | 0.0 |
| `12/coupling_residual_at` | \* |
| `12/dual_gap` | -3.531181391736027e-08 |
| `12/feasible_side_bound` | -332.8878790028561 |
| `12/feasible_side_multipliers/*` | zero |
| `12/frame_deduction` | 0.0 |
| `12/iteration` | 13 |
| `12/linearization` | 0.020911840275036158 |
| `12/min_block_eigenvalue` | 7.825170801026613e-13 |
| `12/min_block_eigenvalue_at` | A\_\_C_1\_\_C_H |
| `12/objective` | 0.02181202392411613 |
| `12/oracle_optimal` | true |
| `12/oracle_pairing` | -332.8878790381679 |
| `12/oracle_status` | optimal |
| `12/row_multiplier_norm` | 0.0 |
| `12/withdrawal` | — |
| `13/acceptance_iterate_exact` | true |
| `13/constraint_row_residual` | 0.0 |
| `13/coupling_residual` | 2.220446049250313e-16 |
| `13/coupling_residual_at` | \* |
| `13/dual_gap` | -8.107631680336763e-09 |
| `13/feasible_side_bound` | -332.8870157257492 |
| `13/feasible_side_multipliers/*` | zero |
| `13/frame_deduction` | 0.0 |
| `13/iteration` | 14 |
| `13/linearization` | 0.021775117370188043 |
| `13/min_block_eigenvalue` | 7.813621646794531e-13 |
| `13/min_block_eigenvalue_at` | A\_\_C_1\_\_C_V |
| `13/objective` | 0.02181202391240551 |
| `13/oracle_optimal` | true |
| `13/oracle_pairing` | -332.8870157338568 |
| `13/oracle_status` | optimal |
| `13/row_multiplier_norm` | 0.0 |
| `13/withdrawal` | — |
| `14/acceptance_iterate_exact` | true |
| `14/constraint_row_residual` | 0.0 |
| `14/coupling_residual` | 0.0 |
| `14/coupling_residual_at` | \* |
| `14/dual_gap` | -5.8294688187743304e-08 |
| `14/feasible_side_bound` | -332.8873441648831 |
| `14/feasible_side_multipliers/*` | zero |
| `14/frame_deduction` | 0.0 |
| `14/iteration` | 15 |
| `14/linearization` | 0.02144667822966084 |
| `14/min_block_eigenvalue` | 7.813102420719765e-13 |
| `14/min_block_eigenvalue_at` | A\_\_C_1\_\_C_D |
| `14/objective` | 0.021812023905790144 |
| `14/oracle_optimal` | true |
| `14/oracle_pairing` | -332.88734422317776 |
| `14/oracle_status` | optimal |
| `14/row_multiplier_norm` | 0.0 |
| `14/withdrawal` | — |
| `15/acceptance_iterate_exact` | true |
| `15/constraint_row_residual` | 0.0 |
| `15/coupling_residual` | 2.220446049250313e-16 |
| `15/coupling_residual_at` | \* |
| `15/dual_gap` | -9.332992578321723e-09 |
| `15/feasible_side_bound` | -332.8878044531205 |
| `15/feasible_side_multipliers/*` | zero |
| `15/frame_deduction` | 0.0 |
| `15/iteration` | 16 |
| `15/linearization` | 0.020986389981765153 |
| `15/min_block_eigenvalue` | 7.813345559903289e-13 |
| `15/min_block_eigenvalue_at` | A\_\_C_1\_\_C_H |
| `15/objective` | 0.021812023895265566 |
| `15/oracle_optimal` | true |
| `15/oracle_pairing` | -332.88780446245346 |
| `15/oracle_status` | optimal |
| `15/row_multiplier_norm` | 0.0 |
| `15/withdrawal` | — |
| `16/acceptance_iterate_exact` | true |
| `16/constraint_row_residual` | 0.0 |
| `16/coupling_residual` | 0.0 |
| `16/coupling_residual_at` | \* |
| `16/dual_gap` | -1.298204387957265e-08 |
| `16/feasible_side_bound` | -332.886986252151 |
| `16/feasible_side_multipliers/*` | zero |
| `16/frame_deduction` | 0.0 |
| `16/iteration` | 17 |
| `16/linearization` | 0.021804590939763956 |
| `16/min_block_eigenvalue` | 7.816393619339021e-13 |
| `16/min_block_eigenvalue_at` | A\_\_C_1\_\_C_nc |
| `16/objective` | 0.021812023883803263 |
| `16/oracle_optimal` | true |
| `16/oracle_pairing` | -332.88698626513303 |
| `16/oracle_status` | optimal |
| `16/row_multiplier_norm` | 0.0 |
| `16/withdrawal` | — |
| `17/acceptance_iterate_exact` | true |
| `17/constraint_row_residual` | 0.0 |
| `17/coupling_residual` | 0.0 |
| `17/coupling_residual_at` | \* |
| `17/dual_gap` | -9.68252956291737e-09 |
| `17/feasible_side_bound` | -332.88699959223806 |
| `17/feasible_side_multipliers/*` | zero |
| `17/frame_deduction` | 0.0 |
| `17/iteration` | 18 |
| `17/linearization` | 0.0217912508446053 |
| `17/min_block_eigenvalue` | 7.813059233617855e-13 |
| `17/min_block_eigenvalue_at` | A\_\_C_1\_\_C_D |
| `17/objective` | 0.02181202387574622 |
| `17/oracle_optimal` | true |
| `17/oracle_pairing` | -332.88699960192054 |
| `17/oracle_status` | optimal |
| `17/row_multiplier_norm` | 0.0 |
| `17/withdrawal` | — |
| `18/acceptance_iterate_exact` | true |
| `18/constraint_row_residual` | 0.0 |
| `18/coupling_residual` | 0.0 |
| `18/coupling_residual_at` | \* |
| `18/dual_gap` | -1.326869117028828e-08 |
| `18/feasible_side_bound` | -332.89343184127785 |
| `18/feasible_side_multipliers/*` | zero |
| `18/frame_deduction` | 0.0 |
| `18/iteration` | 19 |
| `18/linearization` | 0.015359001770887889 |
| `18/min_block_eigenvalue` | 7.81294097631864e-13 |
| `18/min_block_eigenvalue_at` | A\_\_C_D\_\_C_1 |
| `18/objective` | 0.021812023841733898 |
| `18/oracle_optimal` | true |
| `18/oracle_pairing` | -332.8934318545465 |
| `18/oracle_status` | optimal |
| `18/row_multiplier_norm` | 0.0 |
| `18/withdrawal` | — |
| `19/acceptance_iterate_exact` | true |
| `19/constraint_row_residual` | 0.0 |
| `19/coupling_residual` | 1.1102230246251565e-16 |
| `19/coupling_residual_at` | \* |
| `19/dual_gap` | -9.718698102981949e-09 |
| `19/feasible_side_bound` | -332.88822492791263 |
| `19/feasible_side_multipliers/*` | zero |
| `19/frame_deduction` | 0.0 |
| `19/iteration` | 20 |
| `19/linearization` | 0.020565914989297263 |
| `19/min_block_eigenvalue` | 7.855826140041361e-13 |
| `19/min_block_eigenvalue_at` | A\_\_C_1\_\_C_A |
| `19/objective` | 0.021812023695048786 |
| `19/oracle_optimal` | true |
| `19/oracle_pairing` | -332.8882249376313 |
| `19/oracle_status` | optimal |
| `19/row_multiplier_norm` | 0.0 |
| `19/withdrawal` | — |
| `20/acceptance_iterate_exact` | true |
| `20/constraint_row_residual` | 0.0 |
| `20/coupling_residual` | 0.0 |
| `20/coupling_residual_at` | \* |
| `20/dual_gap` | -9.42044903423996e-08 |
| `20/feasible_side_bound` | -332.888028408593 |
| `20/feasible_side_multipliers/*` | zero |
| `20/frame_deduction` | 0.0 |
| `20/iteration` | 21 |
| `20/linearization` | 0.020762434211886102 |
| `20/min_block_eigenvalue` | 7.81280229154883e-13 |
| `20/min_block_eigenvalue_at` | A\_\_C_1\_\_C_A |
| `20/objective` | 0.021812023597975135 |
| `20/oracle_optimal` | true |
| `20/oracle_pairing` | -332.88802850279745 |
| `20/oracle_status` | optimal |
| `20/row_multiplier_norm` | 0.0 |
| `20/withdrawal` | — |
| `21/acceptance_iterate_exact` | true |
| `21/constraint_row_residual` | 0.0 |
| `21/coupling_residual` | 0.0 |
| `21/coupling_residual_at` | \* |
| `21/dual_gap` | -2.7981968742096797e-08 |
| `21/feasible_side_bound` | -332.88743194473676 |
| `21/feasible_side_multipliers/*` | zero |
| `21/frame_deduction` | 0.0 |
| `21/iteration` | 22 |
| `21/linearization` | 0.021358898060031044 |
| `21/min_block_eigenvalue` | 7.812535027799015e-13 |
| `21/min_block_eigenvalue_at` | A\_\_C_1\_\_C_mc |
| `21/objective` | 0.021812023589797634 |
| `21/oracle_optimal` | true |
| `21/oracle_pairing` | -332.88743197271873 |
| `21/oracle_status` | optimal |
| `21/row_multiplier_norm` | 0.0 |
| `21/withdrawal` | — |
| `22/acceptance_iterate_exact` | true |
| `22/constraint_row_residual` | 0.0 |
| `22/coupling_residual` | 1.1102230246251565e-16 |
| `22/coupling_residual_at` | \* |

230 more fields are not shown; see the record.

## <a id="p-.payload.stages.key_rate.search_report"></a>/payload/stages/key_rate/search_report

| Field | Value |
| --- | --- |
| `assessment_count` | 35 |
| `assessment_history` | a list of 35 items (6,509 characters); not shown, see the record |
| `attempts` | a list of 4 items (10,643 characters); not shown, see the record |
| `best_contributing_candidate` | an object of 5 fields (13,173 characters); not shown, see the record |
| `budget_overrun_seconds` | 0.0 |
| `budget_seconds` | 540.0 |
| `capabilities/acceptance` | box |
| `capabilities/block_dimensions` | 1, 2, 1, 1, 1, 1, 1, 1, 2, 4, 2, 2, 2, 2, 2, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1 |
| `capabilities/extra_rows` | false |
| `capabilities/source_mode` | untrusted |
| `converged_relative_gap` | 0.001 |
| `corrective_probes/cold_tau` | 0.0005 |
| `corrective_probes/fallback_blend` | 1e-06 |
| `corrective_probes/progress_fraction` | 0.01 |
| `corrective_probes/rule` | another probe, from the series' own best assessed point, while the series' best assessed bracket rose by more than progress_fraction of the bracket left open above it, the stage has time left and the gap target is unmet |
| `corrective_probes/slice_of_stage` | 0.25 |
| `gap_target` | 1e-10 |
| `iteration_unit` | assessment |
| `last_candidate` | an object of 5 fields (13,173 characters); not shown, see the record |
| `max_iterations` | 200 |
| `max_iterations_caps` | fw |
| `method` | auto |
| `policy` | candidate-portfolio-v5 |
| `preparation_seconds` | 2.093656299985014 |
| `relative_gap` | 1.570091860707826e-05 |
| `resolved_allocations/0/allocated_seconds` | 134.9177499000216 |
| `resolved_allocations/0/assessment_reserve_seconds` | 0.1560133999446407 |
| `resolved_allocations/0/budget_share` | 0.25 |
| `resolved_allocations/0/deadline_seconds` | 135.0907368999906 |
| `resolved_allocations/0/method` | factor |
| `resolved_allocations/0/normalized_remaining_share` | 0.25 |
| `resolved_allocations/0/remaining_seconds` | 539.6709996000864 |
| `resolved_allocations/0/remaining_supported_share` | 1.0 |
| `resolved_allocations/0/resumed` | false |
| `resolved_allocations/0/source` | cold |
| `resolved_allocations/0/stage` | 0 |
| `resolved_allocations/0/start_seconds` | 0.17298699996899813 |
| `resolved_allocations/1/allocated_seconds` | 352.1911943575833 |
| `resolved_allocations/1/assessment_reserve_seconds` | 0.11407466364361232 |
| `resolved_allocations/1/budget_share` | 0.5 |
| `resolved_allocations/1/deadline_seconds` | 363.7903281576 |
| `resolved_allocations/1/method` | entropy |
| `resolved_allocations/1/normalized_remaining_share` | 0.6666666666666666 |
| `resolved_allocations/1/remaining_seconds` | 528.286791536375 |
| `resolved_allocations/1/remaining_supported_share` | 0.75 |
| `resolved_allocations/1/resumed` | false |
| `resolved_allocations/1/source` | cold |
| `resolved_allocations/1/stage` | 1 |
| `resolved_allocations/1/start_seconds` | 11.599133800016716 |
| `resolved_allocations/2/allocated_seconds` | 316.83196784649044 |
| `resolved_allocations/2/assessment_reserve_seconds` | 0.11371085589053109 |
| `resolved_allocations/2/budget_share` | 0.15 |
| `resolved_allocations/2/deadline_seconds` | 328.66497724642977 |
| `resolved_allocations/2/method` | corrective |
| `resolved_allocations/2/normalized_remaining_share` | 0.6 |
| `resolved_allocations/2/remaining_seconds` | 528.0532797441119 |
| `resolved_allocations/2/remaining_supported_share` | 0.25 |
| `resolved_allocations/2/resumed` | false |
| `resolved_allocations/2/source` | best |
| `resolved_allocations/2/stage` | 2 |
| `resolved_allocations/2/start_seconds` | 11.833009399939328 |
| `resolved_schedule/0/budget_share` | 0.25 |
| `resolved_schedule/0/method` | factor |
| `resolved_schedule/0/start` | cold |
| `resolved_schedule/0/unsupported_reason` | — |
| `resolved_schedule/1/budget_share` | 0.5 |
| `resolved_schedule/1/method` | entropy |
| `resolved_schedule/1/start` | cold |
| `resolved_schedule/1/unsupported_reason` | — |
| `resolved_schedule/2/budget_share` | 0.15 |
| `resolved_schedule/2/method` | corrective |
| `resolved_schedule/2/start` | best |
| `resolved_schedule/2/unsupported_reason` | — |
| `resolved_schedule/3/budget_share` | 0.1 |
| `resolved_schedule/3/method` | corrective |
| `resolved_schedule/3/start` | cold |
| `resolved_schedule/3/unsupported_reason` | — |
| `resume_rule` | once the schedule is done, time left (at least 0.05 of the budget) goes to one more run, from the best assessed point, of each search its own deadline cut while it was raising the assessed bracket: the factor search (also for the entropy stage's polish) and a corrective series whose last probe progressed and stopped at its stage deadline, by their schedule shares; a Frank-Wolfe stage is never resumed, its work being capped by max_iterations |
| `returned_candidate_role` | best_original_objective |
| `solver_seconds` | 12.061095400014892 |
| `termination` | relative_gap_met |

## <a id="p-.payload.stages.key_rate.security_gates.accumulation_branch"></a>/payload/stages/key_rate/security_gates/accumulation_branch

`thm:accumulated-entropy`

## <a id="p-.payload.stages.key_rate.security_gates.key_length_permitted"></a>/payload/stages/key_rate/security_gates/key_length_permitted

`true`

## <a id="p-.payload.stages.key_rate.security_gates.source_mode"></a>/payload/stages/key_rate/security_gates/source_mode

`untrusted`

## <a id="p-.payload.stages.key_rate.solver_request"></a>/payload/stages/key_rate/solver_request

| Field | Value |
| --- | --- |
| `budget_seconds` | 600 |
| `certified_evaluation` | on |
| `gap_target` | 1e-10 |
| `max_iterations` | 200 |
| `method` | auto |
| `oracle` | qics |
| `warm_start` | — |

## <a id="p-.payload.stages.key_rate.solver_status"></a>/payload/stages/key_rate/solver_status

`relative_gap_met`

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
| `declared_povm` | an object of 1 fields (6,336 characters); not shown, see the record |
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

## <a id="p-.payload.stages.receiver_construction.receiver_route"></a>/payload/stages/receiver_construction/receiver_route

`element-graph`

## <a id="p-.payload.stages.receiver_construction.route"></a>/payload/stages/receiver_construction/route

`declared_finite_povm`

## <a id="p-.payload.stages.stations"></a>/payload/stages/stations

| Field | Value |
| --- | --- |
| `0` | an object of 7 fields (60,516 characters); not shown, see the record |
| `1` | an object of 7 fields (61,065 characters); not shown, see the record |

## <a id="p-.payload.stages.stations.0"></a>/payload/stages/stations/0

| Field | Value |
| --- | --- |
| `factor` | alice_station |
| `index` | 0 |
| `party` | A |
| `receiver` | an object of 15 fields (29,546 characters); not shown, see the record |
| `receiver_route` | element-graph |
| `reduction` | an object of 20 fields (24,426 characters); not shown, see the record |
| `rows_adaptation` | an object of 8 fields (6,406 characters); not shown, see the record |

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
| **1** | 0.0755598 | -0.0182546 − 1.58077e-18i |
| **2** | -0.0182546 + 1.58077e-18i | 0.0290936 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.0005544 | 0 |
| **2** | 0 | 0.548856 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.50691 | 0 |
| **2** | 0 | 0.00507417 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21584 | 0.215404 + 1.86531e-17i |
| **2** | 0.215404 − 1.86531e-17i | 0.21584 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.201136 | -0.19715 − 1.70723e-17i |
| **2** | -0.19715 + 1.70723e-17i | 0.201136 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | -2.22045e-16 |

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
| **1** | 0.0755598 | -0.0182546 − 1.58077e-18i |
| **2** | -0.0182546 + 1.58077e-18i | 0.0290936 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.0005544 | 0 |
| **2** | 0 | 0.548856 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.50691 | 0 |
| **2** | 0 | 0.00507417 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21584 | 0.215404 + 1.86531e-17i |
| **2** | 0.215404 − 1.86531e-17i | 0.21584 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.201136 | -0.19715 − 1.70723e-17i |
| **2** | -0.19715 + 1.70723e-17i | 0.201136 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -1.11022e-16 | 0 |
| **2** | 0 | -2.22045e-16 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/dark_composed

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 0.999999 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 1.014e-13 |
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
| **1** | 0.0755598 | -0.0182546 − 1.58077e-18i |
| **2** | -0.0182546 + 1.58077e-18i | 0.0290936 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.00055441 | -2.3731e-09 − 2.055e-25i |
| **2** | -2.3731e-09 + 2.055e-25i | 0.548856 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.506909 | -2.3731e-09 − 2.055e-25i |
| **2** | -2.3731e-09 + 2.055e-25i | 0.00507417 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21584 | 0.215404 + 1.8653e-17i |
| **2** | 0.215404 − 1.8653e-17i | 0.21584 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.201136 | -0.19715 − 1.70723e-17i |
| **2** | -0.19715 + 1.70723e-17i | 0.201136 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 3.60532e-07 | 7.11929e-09 + 6.16499e-25i |
| **2** | 7.11929e-09 − 6.16499e-25i | 3.78653e-07 |

## <a id="p-.payload.stages.stations.0.receiver.photon_blocks.settings.0.dark_composed.0"></a>/payload/stages/stations/0/receiver/photon_blocks/settings/0/dark_composed/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 0.999999 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 1.014e-13 |
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
| **1** | 0.0755598 | -0.0182546 − 1.58077e-18i |
| **2** | -0.0182546 + 1.58077e-18i | 0.0290936 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.00055441 | -2.3731e-09 − 2.055e-25i |
| **2** | -2.3731e-09 + 2.055e-25i | 0.548856 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.506909 | -2.3731e-09 − 2.055e-25i |
| **2** | -2.3731e-09 + 2.055e-25i | 0.00507417 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.21584 | 0.215404 + 1.8653e-17i |
| **2** | 0.215404 − 1.8653e-17i | 0.21584 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.201136 | -0.19715 − 1.70723e-17i |
| **2** | -0.19715 + 1.70723e-17i | 0.201136 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 3.60532e-07 | 7.11929e-09 + 6.16499e-25i |
| **2** | 7.11929e-09 − 6.16499e-25i | 3.78653e-07 |

## <a id="p-.payload.stages.stations.0.reduction.target_povm"></a>/payload/stages/stations/0/reduction/target_povm

| Field | Value |
| --- | --- |
| `A/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `A/1` | 2 × 2 matrix, shown below |
| `A/2` | 1 × 1 matrix: 0 |
| `A/3` | 1 × 1 matrix: 0 |
| `A/4` | 1 × 1 matrix: 0 |
| `A/5` | 1 × 1 matrix: 0 |
| `A/6` | 1 × 1 matrix: ≈ 0.597452 (164226344767/274877906944) |
| `A/7` | 1 × 1 matrix: 0 |
| `D/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `D/1` | 2 × 2 matrix, shown below |
| `D/2` | 1 × 1 matrix: 0 |
| `D/3` | 1 × 1 matrix: 0 |
| `D/4` | 1 × 1 matrix: 0 |
| `D/5` | 1 × 1 matrix: ≈ 0.597452 (164226344767/274877906944) |
| `D/6` | 1 × 1 matrix: 0 |
| `D/7` | 1 × 1 matrix: 0 |
| `H/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `H/1` | 2 × 2 matrix, shown below |
| `H/2` | 1 × 1 matrix: 0 |
| `H/3` | 1 × 1 matrix: ≈ 0.597452 (164226344767/274877906944) |
| `H/4` | 1 × 1 matrix: 0 |
| `H/5` | 1 × 1 matrix: 0 |
| `H/6` | 1 × 1 matrix: 0 |
| `H/7` | 1 × 1 matrix: 0 |
| `V/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `V/1` | 2 × 2 matrix, shown below |
| `V/2` | 1 × 1 matrix: 0 |
| `V/3` | 1 × 1 matrix: 0 |
| `V/4` | 1 × 1 matrix: ≈ 0.597452 (164226344767/274877906944) |
| `V/5` | 1 × 1 matrix: 0 |
| `V/6` | 1 × 1 matrix: 0 |
| `V/7` | 1 × 1 matrix: 0 |
| `mc/0` | 1 × 1 matrix: 0 |
| `mc/1` | 2 × 2 matrix, shown below |
| `mc/2` | 1 × 1 matrix: ≈ 0.402548 (110651562177/274877906944) |
| `mc/3` | 1 × 1 matrix: ≈ 0.402548 (110651562177/274877906944) |
| `mc/4` | 1 × 1 matrix: ≈ 0.402548 (110651562177/274877906944) |
| `mc/5` | 1 × 1 matrix: ≈ 0.402548 (110651562177/274877906944) |
| `mc/6` | 1 × 1 matrix: ≈ 0.402548 (110651562177/274877906944) |
| `mc/7` | 1 × 1 matrix: 1 |
| `nc/0` | 1 × 1 matrix: ≈ 0.999999 (34359720501/34359738368) |
| `nc/1` | 2 × 2 matrix, shown below |
| `nc/2` | 1 × 1 matrix: ≈ 0.597452 (164226344767/274877906944) |
| `nc/3` | 1 × 1 matrix: 0 |
| `nc/4` | 1 × 1 matrix: 0 |
| `nc/5` | 1 × 1 matrix: 0 |
| `nc/6` | 1 × 1 matrix: 0 |
| `nc/7` | 1 × 1 matrix: 0 |

*A/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.201136 (221151794755/1099511627776) | ≈ -0.19715 (-216768203135/1099511627776) |
| **2** | ≈ -0.19715 (-216768203135/1099511627776) | ≈ 0.201136 (221151788113/1099511627776) |

*D/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.21584 (237318288083/1099511627776) | ≈ 0.215404 (236839327595/1099511627776) |
| **2** | ≈ 0.215404 (236839327595/1099511627776) | ≈ 0.21584 (237318281441/1099511627776) |

*H/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.00055441 (19049369/34359738368) | ≈ -2.37378e-09 (-1305/549755813888) |
| **2** | ≈ -2.37378e-09 (-1305/549755813888) | ≈ 0.548856 (301736661389/549755813888) |

*V/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.506909 (557352718321/1099511627776) | ≈ -2.37287e-09 (-2609/1099511627776) |
| **2** | ≈ -2.37287e-09 (-2609/1099511627776) | ≈ 0.00507417 (1394777585/274877906944) |

*mc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 3.60532e-07 (396409/1099511627776) | ≈ 7.11952e-09 (1957/274877906944) |
| **2** | ≈ 7.11952e-09 (1957/274877906944) | ≈ 3.78654e-07 (208167/549755813888) |

*nc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.0755598 (2596214075/34359738368) | ≈ -0.0182546 (-20071127069/1099511627776) |
| **2** | ≈ -0.0182546 (-20071127069/1099511627776) | ≈ 0.0290936 (15994354385/549755813888) |

## <a id="p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.0"></a>/payload/stages/stations/0/rows_adaptation/measurement_snaps/0/blocks/0

| Field | Value |
| --- | --- |
| `block` | m=0 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 1.7598295477055413e-12 |
| `displacement_squared` | 1982080023665593455786255301959972285281769/640000000000000000000000000000000000000000000000000000000000000000 |
| `evaluated_off_snap` | true |
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
| `residue_placement/0` | 0, 0, nc |
| `rests_on_assumption` | false |
| `status` | moved |
| `steps` | lattice, completeness-per-entry |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.0.rows_adaptation.measurement_snaps.0.blocks.1"></a>/payload/stages/stations/0/rows_adaptation/measurement_snaps/0/blocks/1

| Field | Value |
| --- | --- |
| `block` | m=1 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 8.72201083027718e-13 |
| `displacement_squared` | 26481175924660751192572908457191198121727853663096930361/34810000000000000000000000000000000000000000000000000000000000000000000000000000 |
| `evaluated_off_snap` | true |
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
| `residue_placement/0` | 0, 0, H |
| `residue_placement/1` | 0, 1, H |
| `residue_placement/2` | 1, 1, H |
| `rests_on_assumption` | false |
| `status` | moved |
| `steps` | lattice, completeness-per-entry |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.1"></a>/payload/stages/stations/1

| Field | Value |
| --- | --- |
| `factor` | bob_station |
| `index` | 1 |
| `party` | B |
| `receiver` | an object of 15 fields (29,905 characters); not shown, see the record |
| `receiver_route` | element-graph |
| `reduction` | an object of 20 fields (24,373 characters); not shown, see the record |
| `rows_adaptation` | an object of 8 fields (6,651 characters); not shown, see the record |

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
| **1** | 0.0732554 | -0.0181086 − 1.67758e-18i |
| **2** | -0.0181086 + 1.67758e-18i | 0.031398 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.0005544 | 0 |
| **2** | 0 | 0.548856 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.50691 | 0 |
| **2** | 0 | 0.00507417 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.243032 | 0.213681 + 1.97954e-17i |
| **2** | 0.213681 − 1.97954e-17i | 0.188648 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.176249 | -0.195572 − 1.81179e-17i |
| **2** | -0.195572 + 1.81179e-17i | 0.226024 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -3.33067e-16 | 0 |
| **2** | 0 | -1.11022e-16 |

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
| **1** | 0.0732554 | -0.0181086 − 1.67758e-18i |
| **2** | -0.0181086 + 1.67758e-18i | 0.031398 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.0005544 | 0 |
| **2** | 0 | 0.548856 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.50691 | 0 |
| **2** | 0 | 0.00507417 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.243032 | 0.213681 + 1.97954e-17i |
| **2** | 0.213681 − 1.97954e-17i | 0.188648 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.176249 | -0.195572 − 1.81179e-17i |
| **2** | -0.195572 + 1.81179e-17i | 0.226024 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | -3.33067e-16 | 0 |
| **2** | 0 | -1.11022e-16 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.dark_composed"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/dark_composed

| Field | Value |
| --- | --- |
| `0/elements/0/block` | 1 × 1 matrix: 0.999999 |
| `0/elements/0/letter` | nc |
| `0/elements/1/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/1/letter` | H |
| `0/elements/2/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/2/letter` | V |
| `0/elements/3/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/3/letter` | D |
| `0/elements/4/block` | 1 × 1 matrix: 1.3e-07 |
| `0/elements/4/letter` | A |
| `0/elements/5/block` | 1 × 1 matrix: 1.014e-13 |
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
| **1** | 0.0732554 | -0.0181085 − 1.67758e-18i |
| **2** | -0.0181085 + 1.67758e-18i | 0.031398 |

*1/elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.000554409 | -2.35411e-09 − 2.18085e-25i |
| **2** | -2.35411e-09 + 2.18085e-25i | 0.548856 |

*1/elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.506909 | -2.35411e-09 − 2.18085e-25i |
| **2** | -2.35411e-09 + 2.18085e-25i | 0.00507417 |

*1/elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.243032 | 0.213681 + 1.97954e-17i |
| **2** | 0.213681 − 1.97954e-17i | 0.188648 |

*1/elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.176249 | -0.195572 − 1.81179e-17i |
| **2** | -0.195572 + 1.81179e-17i | 0.226024 |

*1/elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 3.6143e-07 | 7.06233e-09 + 6.54256e-25i |
| **2** | 7.06233e-09 − 6.54256e-25i | 3.77755e-07 |

## <a id="p-.payload.stages.stations.1.receiver.photon_blocks.settings.0.dark_composed.0"></a>/payload/stages/stations/1/receiver/photon_blocks/settings/0/dark_composed/0

| Field | Value |
| --- | --- |
| `elements/0/block` | 1 × 1 matrix: 0.999999 |
| `elements/0/letter` | nc |
| `elements/1/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/1/letter` | H |
| `elements/2/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/2/letter` | V |
| `elements/3/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/3/letter` | D |
| `elements/4/block` | 1 × 1 matrix: 1.3e-07 |
| `elements/4/letter` | A |
| `elements/5/block` | 1 × 1 matrix: 1.014e-13 |
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
| **1** | 0.0732554 | -0.0181085 − 1.67758e-18i |
| **2** | -0.0181085 + 1.67758e-18i | 0.031398 |

*elements/1/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.000554409 | -2.35411e-09 − 2.18085e-25i |
| **2** | -2.35411e-09 + 2.18085e-25i | 0.548856 |

*elements/2/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.506909 | -2.35411e-09 − 2.18085e-25i |
| **2** | -2.35411e-09 + 2.18085e-25i | 0.00507417 |

*elements/3/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.243032 | 0.213681 + 1.97954e-17i |
| **2** | 0.213681 − 1.97954e-17i | 0.188648 |

*elements/4/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 0.176249 | -0.195572 − 1.81179e-17i |
| **2** | -0.195572 + 1.81179e-17i | 0.226024 |

*elements/5/block*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | 3.6143e-07 | 7.06233e-09 + 6.54256e-25i |
| **2** | 7.06233e-09 − 6.54256e-25i | 3.77755e-07 |

## <a id="p-.payload.stages.stations.1.reduction.target_povm"></a>/payload/stages/stations/1/reduction/target_povm

| Field | Value |
| --- | --- |
| `A/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `A/1` | 2 × 2 matrix, shown below |
| `A/2` | 1 × 1 matrix: 0 |
| `A/3` | 1 × 1 matrix: 0 |
| `A/4` | 1 × 1 matrix: 0 |
| `A/5` | 1 × 1 matrix: 0 |
| `A/6` | 1 × 1 matrix: ≈ 0.59737 (328407866239/549755813888) |
| `A/7` | 1 × 1 matrix: 0 |
| `D/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `D/1` | 2 × 2 matrix, shown below |
| `D/2` | 1 × 1 matrix: 0 |
| `D/3` | 1 × 1 matrix: 0 |
| `D/4` | 1 × 1 matrix: 0 |
| `D/5` | 1 × 1 matrix: ≈ 0.59737 (328407866239/549755813888) |
| `D/6` | 1 × 1 matrix: 0 |
| `D/7` | 1 × 1 matrix: 0 |
| `H/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `H/1` | 2 × 2 matrix, shown below |
| `H/2` | 1 × 1 matrix: 0 |
| `H/3` | 1 × 1 matrix: ≈ 0.59737 (328407866239/549755813888) |
| `H/4` | 1 × 1 matrix: 0 |
| `H/5` | 1 × 1 matrix: 0 |
| `H/6` | 1 × 1 matrix: 0 |
| `H/7` | 1 × 1 matrix: 0 |
| `V/0` | 1 × 1 matrix: ≈ 1.3e-07 (17867/137438953472) |
| `V/1` | 2 × 2 matrix, shown below |
| `V/2` | 1 × 1 matrix: 0 |
| `V/3` | 1 × 1 matrix: 0 |
| `V/4` | 1 × 1 matrix: ≈ 0.59737 (328407866239/549755813888) |
| `V/5` | 1 × 1 matrix: 0 |
| `V/6` | 1 × 1 matrix: 0 |
| `V/7` | 1 × 1 matrix: 0 |
| `mc/0` | 1 × 1 matrix: 0 |
| `mc/1` | 2 × 2 matrix, shown below |
| `mc/2` | 1 × 1 matrix: ≈ 0.40263 (221347947649/549755813888) |
| `mc/3` | 1 × 1 matrix: ≈ 0.40263 (221347947649/549755813888) |
| `mc/4` | 1 × 1 matrix: ≈ 0.40263 (221347947649/549755813888) |
| `mc/5` | 1 × 1 matrix: ≈ 0.40263 (221347947649/549755813888) |
| `mc/6` | 1 × 1 matrix: ≈ 0.40263 (221347947649/549755813888) |
| `mc/7` | 1 × 1 matrix: 1 |
| `nc/0` | 1 × 1 matrix: ≈ 0.999999 (34359720501/34359738368) |
| `nc/1` | 2 × 2 matrix, shown below |
| `nc/2` | 1 × 1 matrix: ≈ 0.59737 (328407866239/549755813888) |
| `nc/3` | 1 × 1 matrix: 0 |
| `nc/4` | 1 × 1 matrix: 0 |
| `nc/5` | 1 × 1 matrix: 0 |
| `nc/6` | 1 × 1 matrix: 0 |
| `nc/7` | 1 × 1 matrix: 0 |

*A/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.176249 (96893719177/549755813888) | ≈ -0.195572 (-107517028755/549755813888) |
| **2** | ≈ -0.195572 (-107517028755/549755813888) | ≈ 0.226024 (248516144513/1099511627776) |

*D/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.243032 (133608190249/549755813888) | ≈ 0.213681 (117472306487/549755813888) |
| **2** | ≈ 0.213681 (117472306487/549755813888) | ≈ 0.188648 (207420189027/1099511627776) |

*H/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.000554409 (76197435/137438953472) | ≈ -2.35377e-09 (-647/274877906944) |
| **2** | ≈ -2.35377e-09 (-647/274877906944) | ≈ 0.548856 (150868330777/274877906944) |

*V/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.506909 (557352717991/1099511627776) | ≈ -2.35377e-09 (-647/274877906944) |
| **2** | ≈ -2.35377e-09 (-647/274877906944) | ≈ 0.00507417 (5579110669/1099511627776) |

*mc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 3.6143e-07 (397397/1099511627776) | ≈ 7.06223e-09 (7765/1099511627776) |
| **2** | ≈ 7.06223e-09 (7765/1099511627776) | ≈ 3.77755e-07 (207673/549755813888) |

*nc/1*

|   | 1 | 2 |
| --- | --- | --- |
| **1** | ≈ 0.0732554 (10068139257/137438953472) | ≈ -0.0181085 (-19910558053/1099511627776) |
| **2** | ≈ -0.0181085 (-19910558053/1099511627776) | ≈ 0.031398 (34522445113/1099511627776) |

## <a id="p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.0"></a>/payload/stages/stations/1/rows_adaptation/measurement_snaps/0/blocks/0

| Field | Value |
| --- | --- |
| `block` | m=0 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | reference |
| `displacement` | 1.7598295477055413e-12 |
| `displacement_squared` | 1982080023665593455786255301959972285281769/640000000000000000000000000000000000000000000000000000000000000000 |
| `evaluated_off_snap` | true |
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
| `residue_placement/0` | 0, 0, nc |
| `rests_on_assumption` | false |
| `status` | moved |
| `steps` | lattice, completeness-per-entry |
| `support_not_preserved` | false |

## <a id="p-.payload.stages.stations.1.rows_adaptation.measurement_snaps.0.blocks.1"></a>/payload/stages/stations/1/rows_adaptation/measurement_snaps/0/blocks/1

| Field | Value |
| --- | --- |
| `block` | m=1 |
| `cause` | — |
| `decided_by` | certiqs_key.foundations.exact.is_positive_semidefinite |
| `defects_ground` | measured |
| `displacement` | 4.258260410949788e-13 |
| `displacement_squared` | 58844241/324518553658426726783156020576256 |
| `evaluated_off_snap` | true |
| `fix` | — |
| `group` | — |
| `group_fix` | — |
| `handed_reference/input_radius` | 1/17014118346046923173168730371588410572800 |
| `handed_reference/kind` | enclosed |
| `handed_reference/largest_radius` | 15030266101460750099/1569275433846670190958947355801916604025588861116008628224 |
| `handed_reference_kind` | enclosed |
| `lift_weight` | — |
| `pre_snap/completeness_residue` | 3.3306690738754696e-16 |
| `pre_snap/hermiticity_defect` | 0.0 |
| `pre_snap/min_eigenvalue` | 3.5879912696449335e-07 |
| `receiver_fix` | — |
| `reference_kind` | none |
| `residue_placement` | \[\] |
| `rests_on_assumption` | false |
| `status` | moved |
| `steps` | lattice |
| `support_not_preserved` | false |

## <a id="p-.payload.statistics_consistency"></a>/payload/statistics_consistency

| Field | Value |
| --- | --- |
| `alpha_0_rule` | lowest_evaluated_order |
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
| `rounds` | 17000000 |
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
