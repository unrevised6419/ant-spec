# Furnica (the Ant): reverse-engineered language specification

Furnica is a Moldovan/Romanian school program from around 2000. Students write programs that move an ant around a 10 × 10 grid, pushing characters into a required layout.

| File | Content |
|---|---|
| [`furnica-language-spec.md`](furnica-language-spec.md) | the full language and runtime specification |
| `binary/Furnica.exe` | the original program (SHA-256 `cdf5378c1fb1ce45d641a8cdae5ac19b3371a7389ee76c6135e67b2e0fe2e6b2`) |
| `tools/DumpApp.java` | Ghidra headless script: creates functions at given addresses (needed for Delphi event handlers) and decompiles an address range |
| `tools/helpers/` | Python helpers: PE offsets, Delphi strings, DFM form parsing. Set `EXE=../../binary/Furnica.exe` before running them |
| `tools/extract_images.py` | extracts every image from the binary: `python3 tools/extract_images.py binary/Furnica.exe <outdir>` |
| `evidence/` | parsed form resources, including the built-in help text (`contents.txt`) |
| `evidence/images/` | all assets, as originals plus PNG copies, indexed in [`evidence/ASSETS.md`](evidence/ASSETS.md) |

The specification was derived from the binary only. A school textbook (Grade 8 Informatics, 2020) was used only for hypotheses, and the spec lists where the textbook is wrong. Every claim is tagged **Observed**, **Inferred**, **Unknown** or **Proposal**, and cites the code address it comes from.

The program does not contain its keywords: it loaded them from localisation files that were not distributed. So the spec defines the language through **keyword roles**, gives the reconstructed Romanian keywords, and proposes English and Russian sets.

## Using this spec

1. Revalidate the spec against `binary/Furnica.exe`; the spec ends with a "How to revalidate" section listing every relevant code address.
2. Implement a grammar and an interpreter. The spec separates the original (faithful) behaviour from recommended corrections, and ends with test cases for both.
