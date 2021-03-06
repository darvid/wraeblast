# wraeblast roadmap

## 1.0

### Library features

* Optimize template rendering and overall performance, including adding
  support for rendering multiple filters within the same process.
* Optimize for bulk filter color palette generation.
* Reduce number of files generated by TTS, investigate feasibility of
  keying by item name (rather than item + chaos value) while maintaining
  caching of duplicate files to avoid unnecessary AWS Polly API calls.
* Provide ability to dedupe item overview dataframes. For example, when
  grouping by value quantile, the same base types could appear in
  multiple groups, unless **base_type** is also grouped. The proposed
  feature would allow conditionally deduping groups, showing only the
  first or last instance of a given field.
* Dedupe filter rules and add heuristics for identifying and warning
  about redundant filter rules.
* Improve item stack size generation: limit stack size iteration to
  only specific subsets of economy overview.

### Filter features

* Presets or separate filter templates for SSF.
* Add playstyle oriented filters - e.g. separate presets or filters for
  essence, sim splinter, scarab, harbinger, etc. farming.
* Fully fleshed out rules for early, mid, and late league.
* Visually and audibly distinctive recipe rules.
* More color options and procedurally generated filters.
* Survive redditor complaints.
