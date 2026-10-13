# Image and sound assets

All assets were extracted from the binary with `../tools/extract_images.py <exe> <outdir>`. The originals (`.bmp`, `.ico`, `.wav`) are kept unchanged, and every image also has a `.png` copy made with macOS `sips`.

Naming:
- `<name>`: an `RT_BITMAP` resource with that name.
- `icon_1`: the main icon (32 × 32, 16 colours).
- `<form>_<component>_<property>`: a bitmap stored inside a Delphi form (DFM). `glyph` is a button image; `picture` is a `TImage`.
- `_imagelist0` / `_imagelist1`: an image-list strip and its mask.

Transparency: the original Delphi controls make one colour transparent, normally the colour of the bottom-left pixel. The PNGs are not made transparent.

## Files (`images/`)

| File | Size | Use |
|---|---|---|
| `sus`, `jos`, `stinga`, `dreapta` | 33 × 33, 8-bit | ant sprite facing up / down / left / right (loaded by facing; see spec §5.1) |
| `tmainform_Image2_picture` | 33 × 33 | the ant image on the form at design time |
| `tmainform_{Up,Down,Left,Right}Button_glyph` | 32 × 16 | arrow buttons "Setare pozitie" (two 16 × 16 frames: normal and disabled) |
| `tmainform_{NewFile,OpenFile,SaveFile,ExitProgram}_glyph` | 32 × 16 | toolbar: New, Open, Save, Exit |
| `tmainform_{CheckButton,RunButton,StopButton}_glyph` | 32 × 16 | toolbar: syntax check, run, stop |
| `tmainform_SpeedButton2_glyph` | 19 × 19 | speed/configuration button |
| `tmainform_SpeedButton11_glyph` | 32 × 16 | "Rotire" (rotate the ant sprite in setup mode) |
| `taboutbox_Image1_picture` | 183 × 172 | About-box picture |
| `icon_1` | 32 × 32 | application icon |

Furnica contains no sounds. Its remaining bitmaps (`BB*`) and cursors are stock Delphi VCL resources and were skipped.
