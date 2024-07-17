SchemaManager

SchemaManager will be basis upon which suite of tools will be built.
First look to see whether SchemaManager is possible.
Captures many VFX filesystems, but not enough just yet. Next re-write should capture them 🤞🤞

Shorthand notes:
Usage:
- convert the schema string to UNIX style path delimeters
- rip out the anchor
- UPTO 3 levels of delimiters - usually '/', '_', '.'
- Walk the schema string and break it down to 3 levels
- Allow optional tokens or 1X multidelimeted string before the version token

Todo:
- still first look
- allow multi level optionals, notably for pipelines that account for userspace and often use 2 levels of path depth
- rework again to reduce repetition in code
- version inspection
- allow for major/minor versioning variants
- YAML import
- Proper docs on next re-write.

Test strings for app_qt:

//jobs.local/sharename/shows/{@show}{/@sequence}{/@shot}/{#product}{/@role}{?/@user}{/@show}{_@sequence}{_@shot}{_@role}{_@asset}{?_@variant}{_@version[v3_2]}{_@resolution}{/@show}{_@sequence}{_@shot}{_@role}{_@asset}{?_@variant}{_@version[v3_2]}{_@resolution}{?.#padding}{.#extension}

