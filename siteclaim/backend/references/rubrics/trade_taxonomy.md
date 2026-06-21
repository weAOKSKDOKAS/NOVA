# Trade Taxonomy — canonical HK construction trades (v1)

The canonical list of trades a tender is split into. **Layer 1 checks the scope
split against this list** (deterministic): a returned trade must map to one of
these canonical names, or it is flagged for review. The LLM may use richer
phrasing, but every `TradeWorkPackage.trade` is normalised to a canonical key here.

| Canonical key | Label | Typical scope |
| --- | --- | --- |
| `foundation_substructure` | Foundation & substructure | Piling, pile caps, ground beams, basement |
| `structural` | Structural steel | Steelwork, connections, metal decking |
| `reinforced_concrete` | Reinforced concrete | Formwork, rebar fixing, concreting |
| `electrical` | Electrical | LV distribution, containment, power & lighting |
| `mechanical_plumbing` | Mechanical & plumbing | HVAC, ductwork, pipework, drainage |
| `fire_services` | Fire services | Sprinklers, hydrants, detection & alarm |
| `joinery_fitting_out` | Joinery & fitting-out | Partitions, ceilings, doors, finishes |
| `builders_work` | Builder's work | Builder's work in connection (BWIC), making good |
| `external_works` | External works | Roads, drainage, landscaping, hardstanding |

## Normalisation notes
- Match is case-insensitive on the label or the key; near-synonyms map to the
  nearest canonical key (e.g. "E&M — electrical" → `electrical`).
- A trade with no match is **not** silently dropped — it is surfaced as an
  unmapped trade for human review.
- The taxonomy is versioned; bump the version when a key is added or renamed.
