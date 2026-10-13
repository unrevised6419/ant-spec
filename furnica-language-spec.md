# Furnica (the Ant executor): language and runtime specification

Version 1.1 · 2026-10-13 · reverse-engineered from the original Windows program; revalidated from scratch against the binary (fresh Ghidra decompilation and RTL disassembly)

This document describes the programming language of **Furnica** ("Executantul ANT", window caption `Executantul "ANT"`, About box `Ant v2.00`). It was written so that the language can be reimplemented, for example as a web app, and so that every claim can be checked again against the original binary.

School textbooks describe this language together with other teaching executors and simplify it; where the textbook and this program disagree, this document follows the program.

---

## 0. How to read this document

### 0.1 Source of truth

| Artifact | Identity |
|---|---|
| `Furnica.exe` | 557,568 bytes, SHA-256 `cdf5378c1fb1ce45d641a8cdae5ac19b3371a7389ee76c6135e67b2e0fe2e6b2`, file date 2000-01-19 (from the distribution archive; the PE `TimeDateStamp` is the fixed Delphi value 708992537 and the About box says 06.12.1999) |
| Format | PE32, Intel 80386, Windows GUI, Borland Delphi (VCL), image base `0x400000`, `CODE` section at VA `0x401000` |

Everything here comes from that binary: Ghidra 12.1.4 decompilation, raw disassembly, the Delphi form resources (DFM, binary `TPF0` format) and the RTTI method tables. The program was never executed, so all runtime behaviour is derived from static analysis.

The binary is compiled with range checking (`{$R+}`) and overflow checking (`{$Q+}`): array indexes and integer additions in the application code are guarded by calls to the RTL error routines 0x402c78 (runtime error 4) and 0x402c80 (runtime error 5). [O]

A secondary source, used only to form hypotheses, is the Moldovan Grade 8 Informatics textbook (2020, Romanian edition), chapter 2. It is simplified and often wrong about this program. Section 12 lists where it differs.

### 0.2 Evidence tags

Every non-trivial claim has a tag and, where possible, the address it comes from.

- **[O] Observed**: read directly from code or data at the cited address.
- **[I] Inferred**: follows from observed facts, but the exact value is not in the binary.
- **[U] Unknown**: cannot be determined from the binary.
- **[P] Proposal**: a design choice offered by this document for a reimplementation. It is not a property of the original.

Addresses are code virtual addresses (VAs) unless marked "str" (string literal) or "res" (resource).

### 0.3 The five facts that matter most

1. **No keyword text is compiled into the program.** All keywords, every message and every UI caption are read at startup from a localisation file (`romana.lng`, `rusa.lng` or `engleza.lng`), and none of these files ships with the program. The language is therefore defined by **keyword roles**, and each localisation fills those roles with words. [O] `ReadLanguage` @0x457d70.
2. **Romanian is the only localisation that can be reconstructed**, from two places: the design-time captions of the keyword-insert buttons and the built-in Romanian help text. These two sources agree exactly. [I] (§2.3)
3. **The language is line-based.** One statement per line, and blocks end with a dedicated end-marker line. [O]
4. **Keywords are matched case-insensitively for ASCII letters only.** Diacritics are compared byte for byte, and the original keywords contain none. [O]
5. **The original interpreter has many bugs** (§9). A reimplementation must choose, quirk by quirk, between *faithful* and *corrected* behaviour.

---

## 1. Overview

The ant lives on a **10 × 10 grid** of cells. Some cells hold single printable characters ("objects"). The ant moves one cell up, down, left or right. If it walks into an object, it pushes the object one cell further when that is possible. Typical tasks ask students to rearrange the characters, for example to spell `MAMA`.

A program looks like this (Romanian localisation):

```
PROCEDURA LAPERETE
CIT NU_E_MARGINE EXECUTA
DREAPTA
SFIRSIT CIT
SFIRSIT PROCEDURA
INCEPUT
REPETA 3 ORI
JOS
SFIRSIT REPETA
LAPERETE
DACA E_MARGINE ATUNCI SUS ALTFEL JOS
SFIRSIT
```

---

## 2. Localisation model and keyword roles

### 2.1 Localisation file format [O] `ReadLanguage` @0x457d70

The original `.lng` file is plain single-byte text, read with Pascal `Readln`: one line goes into one string, so a value may contain spaces. It holds exactly **61 lines**, in this order:

| Lines | Group | Globals (VA) | Content |
|---|---|---|---|
| 1–11 | A[1..11] | 0x45d8c4 + 4·(i−1) | whole-line keywords and conditions |
| 12–19 | B[1..8] | 0x45d8f0 + 4·(i−1) | statement-head and structural words |
| 20–31 | C[1..12] | 0x45d910 + 4·(i−1) | messages |
| 32–61 | D[1..30] | 0x45d940 + 4·(i−1) | UI captions |

The language is selected by `language.cfg`. Its first line is `ROM`, `RUS` or `ENG` (exact, case-sensitive comparison), which maps to `romana.lng`, `rusa.lng` or `engleza.lng`. [O] `SetLanguage` @0x4583b4, str 0x458548–0x458594. Any other first line loads nothing and shows no message. [O] `ReadLanguage` rewrites `language.cfg` with the current code every time it runs, so the choice persists. [O] 0x457d9d–0x457e43.

If `language.cfg` or the chosen `.lng` file is missing, the original calls `ShowMessage('')` and then `MainForm.Close` [O] (0x4584f5, 0x4582f2). At startup this happens inside `FormCreate`, before `Application.CreateForm` has registered the main form (0x4436e8), so `Close` does not terminate the program: it runs `FormCloseQuery`, which asks the exit question C12 with an empty text, and on Yes only hides the form. [O] The window then most likely opens anyway with the design-time captions and every keyword slot empty, so nothing parses. [I] Either way, the shipped zip on its own is not usable.

Switching language from the menu [O] 0x45b400 / 0x45b4f4 / 0x45b5e8:
- clears all 100 grid cells, sets cell(1,1) := `'*'`, and calls `FormCreate` again; that re-runs `SetLanguage` (so the file is read twice), clears the program, deletes `!temp.tmp` and puts the ant at (1,1) facing down;
- checks and disables the chosen menu item;
- if the new `.lng` is missing, the exit question C12 is asked and Yes closes the program.

**[P]** A reimplementation should keep the *role* model and supply its own keyword sets. It does not need to copy the 61-line file layout.

### 2.2 Keyword roles

The role of each slot is **[O]**, taken from how the code uses the global. The Romanian spelling is **[I]**, for the reasons given in §2.3.

| Role ID | Slot (global) | Role | Romanian keyword [I] | Where the role is observed |
|---|---|---|---|---|
| `BEGIN` | A1 (0x45d8c4) | start of the main program, alone on its line | `INCEPUT` | checker 0x459bba |
| `END` | A2 (0x45d8c8) | end of the main program, alone on its line; also the first word of the REPEAT/WHILE end markers | `SFIRSIT` | 0x459bdd, 0x459868, 0x456626 |
| `LEFT` | A3 (0x45d8cc) | move left | `STINGA` | dispatch to 0x454bf4 |
| `RIGHT` | A4 (0x45d8d0) | move right | `DREAPTA` | dispatch to 0x4545cc |
| `UP` | A5 (0x45d8d4) | move up | `SUS` | dispatch to 0x45521c |
| `DOWN` | A6 (0x45d8d8) | move down | `JOS` | dispatch to 0x455844 |
| `END_WHILE` | A7 (0x45d8dc) | whole-line end marker of a WHILE block | `SFIRSIT CIT` | WHILE scan 0x4567b0 |
| `END_REPEAT` | A8 (0x45d8e0) | whole-line end marker of a REPEAT block | `SFIRSIT REPETA` | REPEAT scan 0x4563dc |
| `END_PROC` | A9 (0x45d8e4) | whole-line end marker of a procedure | `SFIRSIT PROCEDURA` | CALL 0x4567f4 |
| `AT_EDGE` | A10 (0x45d8e8) | condition: facing the edge | `E_MARGINE` | IF / WHILE |
| `NOT_AT_EDGE` | A11 (0x45d8ec) | condition: not facing the edge | `NU_E_MARGINE` | IF / WHILE |
| `REPEAT` | B1 (0x45d8f0) | REPEAT head word; second word of the end-repeat line in the balance check | `REPETA` | 0x459c51, 0x459868 |
| `TIMES` | B2 (0x45d8f4) | third word of the REPEAT line (required) | `ORI` | 0x459567 |
| `IF` | B3 (0x45d8f8) | IF head word | `DACA` | 0x459c68 |
| `THEN` | B4 (0x45d8fc) | third word of the IF line (required) | `ATUNCI` | 0x459609 |
| `WHILE` | B5 (0x45d900) | WHILE head word; second word of the end-while line | `CIT` | 0x459c7f, 0x456642 |
| `DO` | B6 (0x45d904) | third word of the WHILE line (required) | `EXECUTA` | 0x459844 |
| `ELSE` | B7 (0x45d908) | fifth word of the IF line (optional) | `ALTFEL` | checker only, 0x45978c |
| `PROC` | B8 (0x45d90c) | procedure header word | `PROCEDURA` | 0x459c96 |

Constraints between roles [O]/[I]:
- `END_REPEAT` must equal `END` + one space + `REPEAT`. The balance check (0x459868) recognises an end-repeat line as first word `END` followed by `REPEAT`, while the runtime stops a REPEAT body at the line equal to `END_REPEAT`. Both must agree for REPEAT to work.
- `END_WHILE` must equal `END` + one space + `WHILE`. Inside the body, the WHILE executor recognises the end line as first word `END` with the rest of the line equal to `WHILE` (0x456626–0x45664f); only the final scan that sets PC compares whole lines with `END_WHILE` (0x4567b0).
- The syntax checker never reads `END_WHILE`, `END_REPEAT` or `END_PROC` except as whole lines that are valid on their own; their only run-time uses are 0x4567b0, 0x4563dc and 0x456a2d.
- Conditions are single words (no space), because they are read with the next-word function (§3.2).
- The original compares keywords exactly as stored, without upper-casing them (§3.1), so every keyword must be written in **upper-case ASCII**.

**There is no call keyword.** A procedure is called by writing its bare name on a line. `EXECUTA` belongs only to the WHILE header (`CIT … EXECUTA`). [O] 0x459a68; the help text says so explicitly (§2.3).

### 2.3 Why the Romanian spellings are trusted

At startup, `ReadLanguage` overwrites the captions of 17 keyword-insert buttons (SpeedButton1–19) with the values from the `.lng` file. Their **design-time** captions, stored in the DFM resource `TMAINFORM`, are therefore the Romanian defaults [O]:
`Inceput`, `Sfirsit`, `Stinga`, `Dreapta`, `Sus`, `Jos`, `Cit`, `Daca`, `E_margine`, `Nu_e_margine`, `Executa`, `Atunci`, `Altfel`, `Repeta`, `Ori`, `Procedura`, plus `Sfirsit...`.

The built-in Romanian help text (DFM `TCONTENTSFORM.Memo1`; the text is not localised, only the help window caption D23 and its Exit button D24 are) uses exactly the upper-case forms in §2.2. Verbatim, in the original spelling (no diacritics; `SFIRSIT` and `STINGA` with *i*). In the DFM, the lines `SFIRSIT REPETA`, `...set de`, `<intructiune> in`, `plasate`, `intotdeauna`, `pot intra`, `procedurii se` and `excluzind` end in one trailing space, not shown below:

```
Comenzile simple:

INCEPUT - indica inceputul programului
SFIRSIT - indica sfirsitul programului
SUS - misca furnica cu o pozitie in sus
JOS - misca furnica cu o pozitie in jos
DREAPTA - misca furnica cu o pozitie in dreapta
STINGA - misca furnica cu o pozitie in stinga

Comenzile compuse:

REPETA <N> ORI
...
SFIRSIT REPETA
- este structura repetitiva ce repeta un anumit set de
instructiuni de <n> ori

CIT <conditie> EXECUTA
...
SFIRSIT CIT
- este o structura repetitiva ce repeta un anumit set de
instructiuni pina atunci cind se va indeplini <CONDITIE>

DACA <conditie> ATUNCI <instructiune> ALTFEL <instructiune>
- este un tip de ramificator ce va indeplini <intructiune> in
dependenta
daca se indeplineste conditie sau nu.

<conditie> - poate avea valorile E_MARGINE sau NU_E_MARGINE

PROCEDURA <nume>
...
SFIRSIT PROCEDURA
- in acest fel se declara propcedurile. Ele sunt plasate
intotdeauna
inaintea instructiunii inceput. In corpul procedurii pot intra
toate instructiunile
descrise mai sus, cit si alte proceduri. Apelul procedurii se
face in program
scriind doar numele ei.

<nume> - poate contine atit litere cit si cifre, excluzind
semnele speciale si
spatiile.
```

The help also documents editor shortcuts: Ctrl+Ins copies, Shift+Ins pastes, and Shift+Del cuts the selected text.

### 2.4 Keyword sets for a reimplementation

| Role | Romanian (original) [I] | English [P] | Russian [P] |
|---|---|---|---|
| BEGIN | `INCEPUT` | `BEGIN` | `НАЧАЛО` |
| END | `SFIRSIT` | `END` | `КОНЕЦ` |
| UP / DOWN / LEFT / RIGHT | `SUS` / `JOS` / `STINGA` / `DREAPTA` | `UP` / `DOWN` / `LEFT` / `RIGHT` | `ВВЕРХ` / `ВНИЗ` / `ВЛЕВО` / `ВПРАВО` |
| REPEAT … TIMES | `REPETA` … `ORI` | `REPEAT` … `TIMES` | `ПОВТОРИ` … `РАЗ` |
| END_REPEAT | `SFIRSIT REPETA` | `END REPEAT` | `КОНЕЦ ПОВТОРИ` |
| WHILE … DO | `CIT` … `EXECUTA` | `WHILE` … `DO` | `ПОКА` … `ДЕЛАЙ` |
| END_WHILE | `SFIRSIT CIT` | `END WHILE` | `КОНЕЦ ПОКА` |
| IF … THEN … ELSE | `DACA` … `ATUNCI` … `ALTFEL` | `IF` … `THEN` … `ELSE` | `ЕСЛИ` … `ТО` … `ИНАЧЕ` |
| PROC / END_PROC | `PROCEDURA` / `SFIRSIT PROCEDURA` | `PROCEDURE` / `END PROCEDURE` | `ПРОЦЕДУРА` / `КОНЕЦ ПРОЦЕДУРА` |
| AT_EDGE / NOT_AT_EDGE | `E_MARGINE` / `NU_E_MARGINE` | `AT_EDGE` / `NOT_AT_EDGE` | `У_КРАЯ` / `НЕ_У_КРАЯ` |

The English and Russian sets are **proposals**: the original Russian and English files are unknown [U]. In the original, Cyrillic keywords would be case-sensitive, because its upper-casing is ASCII-only [I]. **[P]** Use Unicode-aware upper-casing in a reimplementation.

**[P]** Diacritic tolerance: accepting `ÎNCEPUT`/`INCEPUT`, `STÂNGA`/`STINGA` and `SFÂRŞIT`/`SFIRSIT`/`SFARSIT` as aliases helps students who follow the textbook. The original does not do this.

---

## 3. Lexical rules

### 3.1 Line normalisation [O] `Normalize` @0x4543a4

The program text is the list of editor lines, separated by CRLF. Before analysis, each line goes through these steps:
1. Every byte is upper-cased with `System.UpCase`, which converts only ASCII `a`–`z` (0x4027f4: `cmp al,'a'; jb; cmp al,'z'; ja; sub al,20h`).
2. Leading spaces (0x20) are removed.
3. Each run of spaces is collapsed to one space.
4. If the last character is a space, it is removed. Because runs were already collapsed, this removes all trailing spaces.

Keywords from the localisation file are compared **as stored** with an exact byte comparison (`LStrCmp` 0x403c64).

Consequences:
- Source text is case-insensitive for ASCII letters: `sus`, `Sus` and `SUS` are the same. [O]
- **Only the space character 0x20 is whitespace.** A TAB is an ordinary character, so a line indented with a tab does not match and is a **syntax error**. [O]/[I]
- Letters with diacritics are neither upper-cased nor folded. [O]

### 3.2 Words [O] `NextWord` @0x454508

`NextWord(line)` returns the characters up to the first space (or the end of the line), removes them from the line, and then removes one more character (the space). Called repeatedly, it yields successive words. If the line has no space, it returns the whole line and leaves it empty; on an empty line it returns `''`.

### 3.3 Tokens and other lexical facts

| Item | Rule | Evidence |
|---|---|---|
| Statement separator | The line break. Exactly one statement per line. | [O] 0x459b1c |
| Blank lines | A line that is empty after normalisation is allowed anywhere. | [O] 0x459c24 |
| Comments | **None.** Every non-blank line must be a valid statement or marker. | [O] 0x459b1c |
| Integer (REPEAT count) | Checked with Delphi `Val` (0x4029e0): the parse code must be 0 and the value ≥ 0 (0x459534–0x459544). At run time it is read with `StrToInt` (0x407c18). `Val` also accepts a leading `+`, `-0`, and hexadecimal with `$`, `X` or `0X` (so `x1f` and `0x1f` work after upper-casing). Hex values are not sign-checked: `$80000000` and above become negative and are rejected. `-$5` and an empty count are rejected. | [O] |
| Procedure name | Any run of non-space characters. Nothing checks for letters or digits, so diacritics, `_` and punctuation are all accepted, compared after ASCII upper-casing. The help text *recommends* letters and digits only. | [O] 0x45997c, 0x459a68 |
| Reserved words | None. In the checker a keyword line is already valid before procedure names are looked at. At run time a procedure named like a keyword is **not** shadowed: the main loop, procedure bodies and IF branches always look up the procedure table after the keyword dispatch, so a procedure named `SUS` runs *in addition to* the move. | [O] 0x45a06a–0x45a0bd, 0x4569d7–0x456a1a, 0x455ff2–0x45609f |

**[P]** A reimplementation may accept tabs and other Unicode whitespace, add `//` comments as an extension, and restrict names to `letter (letter | digit | _)*`. Mark these as extensions.

---

## 4. Syntax

### 4.1 Program structure

```
{ procedure definitions }          ← optional, must come before use (see 4.4)
BEGIN
{ statements }
END
```

### 4.2 EBNF (on normalised lines)

`NL` = line break, `SP` = exactly one space (after normalisation), `K(role)` = the keyword of the current localisation.

```ebnf
program     = { blank NL } { procdef } K(BEGIN) NL { line NL } K(END) [ NL { any_line NL } ] ;
procdef     = K(PROC) SP name NL { line NL } K(END_PROC) NL ;
line        = stmt | blank ;
stmt        = move | call | if_line | repeat | while ;

move        = K(UP) | K(DOWN) | K(LEFT) | K(RIGHT) ;          (* alone on the line *)
call        = name ;                                           (* alone on the line; must be defined above *)

if_line     = K(IF) SP cond SP K(THEN) SP branch
              [ SP K(ELSE) [ SP branch ] ] ;                   (* the whole IF on ONE line *)
branch      = move | name ;                                    (* exactly one word *)

repeat      = K(REPEAT) SP count SP K(TIMES) { SP word } NL
              { line NL }
              K(END_REPEAT) ;
while       = K(WHILE) SP cond SP K(DO) { SP word } NL
              { line NL }
              K(END_WHILE) ;

cond        = K(AT_EDGE) | K(NOT_AT_EDGE) ;                    (* one word *)
count       = unsigned_integer ;                               (* Delphi Val; >= 0 *)
name        = nonspace { nonspace } ;
blank       = "" ;
```

The original checks each line separately (§4.3), so this grammar is the **intended** structure. It is stricter than what the original accepts. §4.5 lists what the original accepts beyond it.

### 4.3 How the original checks syntax [O] `SyntaxCheck` @0x459b1c (disassembly 0x459bb2–0x459e36)

The check runs line by line, from line 0 up to and including line index `Count` (one past the last line, which reads as empty and is valid), and **stops at the first invalid line** (loop test 0x459cda–0x459ce6):
1. `L = Normalize(line i)`.
2. If `L == BEGIN`, record `beginLine = i` and increment `nBegin`. If `L == END`, record `endLine = i` and increment `nEnd`. Both keep the *last* occurrence.
3. The line is valid if `L` is empty or equals any of the A-slot keywords (A1–A11) as a whole line.
4. Otherwise `w = NextWord(L)`, followed by four **independent** tests on `w` (0x459c4e–0x459ca9), in this order:
   - `w == REPEAT`: `CheckRepeat` (0x459508). The next word must parse as an integer ≥ 0, and the word after that must be `TIMES`. The rest of the line is ignored.
   - `w == IF`: `CheckIf` (0x45958c), see §4.6.
   - `w == WHILE`: `CheckWhile` (0x4597e4). The next word must be `AT_EDGE` or `NOT_AT_EDGE`, and the word after that must be `DO`. The rest of the line is ignored.
   - `w == PROC`: `CheckProc` (0x45997c). The rest of the line must be exactly one word, the name. The procedure is then **registered** in the procedure table: the 16-bit counter 0x45e22c is incremented (0x4599d3), the name goes to 0x45da24 + 8·(k−1) and the header line index + 1 to the word at 0x45da28 + 8·(k−1) (0x459a38). Duplicates are not checked.
5. If the line is still invalid: `CheckCall` (0x459a68) accepts it if the whole line equals a registered procedure name.

**Cross-keyword quirk [O].** `CheckRepeat`, `CheckIf` and `CheckWhile` read their words into the same variable `w` that holds the first word, and the line-valid flag is only ever set, never cleared. A checker that fails can leave a later head keyword in `w`, and that keyword's checker then runs on the rest of the line. Lines accepted this way include:
- `REPETA 3 DACA E_MARGINE ATUNCI SUS`
- `REPETA 1 CIT E_MARGINE EXECUTA`
- `REPETA 1 PROCEDURA X` and `CIT E_MARGINE PROCEDURA X`, which also register `X`.

After the loop, `CheckBalance` (0x459868) scans lines 0..Count−1 (ignoring where the main loop stopped). It counts the lines whose first word is `REPEAT`, and the lines whose first word is `END` and whose remainder is exactly `REPEAT`. Only the counts are compared, not the order. If they differ, the program is flagged unbalanced, which is an **error** (it stops Run), not a warning. **Only REPEAT blocks are balanced.** Missing WHILE or procedure end markers are not detected by the checker. [O]

**Result flag [O].** `SyntaxCheck` reports failure through a byte the caller passes by reference, and only ever writes 1 to it (0x459d05: an invalid line or unbalanced REPEAT), never 0. `RunButtonClick` passes an **uninitialised** stack byte (`[EBP−5]`, 0x459ec9) and refuses to run if it is non-zero (0x459eda). So whether a valid program runs depends on leftover stack contents; when it does not, no message is shown.

### 4.4 Ordering rules
- A procedure must be **defined above** any line that calls it, because calls are validated against the procedures registered so far. [O] Because the table is never reset (§9 #10), a name registered by any earlier Check or Run in the same session also passes.
- The help text says procedures go before `BEGIN` [O], but the checker only enforces define-before-use. [O]
- Procedures are not meant to be nested in each other's text, but the checker accepts a `PROC` header anywhere, including inside another procedure's body. A procedure body may call other procedures. [O]

### 4.5 What the original accepts beyond the grammar [O]
- A lone `END_WHILE`, `END_REPEAT`, `END_PROC`, `AT_EDGE` or `NOT_AT_EDGE` line, anywhere. At run time it does nothing.
- Procedure definitions anywhere, even after `END`.
- `BEGIN` and `END` lines counted anywhere in the file. Missing, duplicate or out-of-order markers only produce *warnings* (§8, C2–C6), which do not stop Run.
- Extra words after `REPEAT n TIMES` and after `WHILE cond DO`.
- The cross-keyword lines of §4.3, the IF lines of §4.6, the extra number forms of §3.3, and blank lines anywhere (including between procedure definitions).

**[P]** A reimplementation should reject all of these, or warn and continue in a clearly labelled compatibility mode.

### 4.6 The IF line in detail [O] `CheckIf` @0x45958c

`L` is the rest of the line after `IF`.
1. `cond = NextWord`; it must be `AT_EDGE` or `NOT_AT_EDGE`.
2. `NextWord` must be `THEN`.
3. `instr1 = NextWord`. It is valid if it is an A-slot keyword or a registered procedure name.
4. If words remain: `w5 = NextWord`, then `instr2 = NextWord`. Only then (0x4596e5) is the rest tested: if no words remain, the else part counts as valid **without checking `instr2`**. Otherwise `instr2` is valid if it is an A-slot keyword or a procedure name.
5. The line is invalid unless both branches are valid. `w5` must equal `ELSE` **only if** more words remain after `instr2` (0x45977d–0x45979f).

The flag that records "`instr2` is valid" (`[EBP−3]`) is **never initialised**; the code only ever sets it to 1 (0x4596ee, 0x459719, 0x459762). Its starting value is a leftover stack byte, so when `instr2` is invalid *and* words follow it, acceptance is not deterministic. [O]

Observed consequences:
- `ELSE` is optional.
- `DACA E_MARGINE ATUNCI SUS ALTFEL` (ELSE with no branch) is accepted.
- `DACA E_MARGINE ATUNCI SUS ALTFEL FOO` is accepted even when `FOO` is not a procedure: with exactly two words after `instr1`, the else branch is not checked.
- `DACA E_MARGINE ATUNCI SUS JOS DREAPTA` is accepted: `w5 = JOS` is not checked, and `DREAPTA` runs as the else branch.
- In `… ALTFEL x y …`, the word `ALTFEL` is checked and `x` is checked (subject to the uninitialised flag); the words after `x` are ignored.
- Each branch is **exactly one word**: a move or a procedure name. A branch can also be any other single-word A-slot keyword (such as `INCEPUT`), which is accepted but does nothing at run time.
- **The whole IF must be on one line.** A line that starts with `ATUNCI` or `ALTFEL` is invalid, unless a procedure with that name is registered.
- To run several statements in a branch, put them in a procedure and use its name as the branch.

---

## 5. Runtime model

### 5.1 State [O]

| Item | Global (VA) | Values |
|---|---|---|
| Ant column X | 0x45e224 | 1..10, left → right |
| Ant row Y | 0x45e228 | 1..10, top → bottom |
| Facing | 0x45e238 | 1 = down, 2 = left, 3 = up, 4 = right; also selects the sprite (`jos`, `stinga`, `sus`, `dreapta`, str 0x457d40–0x457d68) |
| Grid | 0x45d9c0 | cell(X,Y) is the byte at 0x45d9c0 + 10·(Y−1) + (X−1); 0 = empty, `'*'` = the ant, any other byte = an object character |
| Error / stop flag | 0x45e240 | set by failed moves, Stop and running past the last line (REPEAT 0x456266, WHILE 0x456506, CALL 0x4568cb); cleared only at the start of Run (0x459ed3, 0x459f52) and by the arrow buttons, **not** at the end of a run |
| Program counter | 0x45e248 | 0-based editor line index |
| Move delay | 0x45d9b8 | 16-bit, milliseconds; 100, set at program entry (0x45b92d) |

Initial state [O] `FormCreate` @0x45a3c0:
- The ant is at **(1,1)**, the top-left cell, facing **down** (1).
- The grid is empty apart from `'*'` at (1,1).
- The editor is empty.
- A leftover `!temp.tmp` is deleted.

Cells are 35 px in the original UI (`Image1MouseDown`: cell = (x div 35 + 1, y div 35 + 1)). [O]

### 5.2 Moves [O] LEFT 0x454bf4 / RIGHT 0x4545cc / UP 0x45521c / DOWN 0x455844

Described for RIGHT; DOWN is identical on Y. LEFT (X−1, wall at X<1) and UP (Y−1, wall at Y<1) test the same three failures in a different order (wall, push off the edge, two objects), with the same outcome. Steps 3–5 are independent tests, not an else-chain; the result is the same because step 2 already emptied the ant's cell.
1. Set facing := right (4) and update the sprite. **Facing changes even if the move then fails.**
2. cell(X,Y) := 0; X := X+1.
3. If X > 10 → **error** (wall), X := X−1.
4. Else, if X < 10 and cell(X,Y) ≠ 0 and cell(X+1,Y) ≠ 0 → **error** (two objects in a row cannot be pushed), X := X−1.
5. Else, if X = 10 and cell(X,Y) ≠ 0 → **error** (an object cannot be pushed off the grid), X := X−1.
6. If there is no error and cell(X,Y) ≠ 0 → **push**: cell(X+1,Y) := cell(X,Y), cell(X,Y) := 0. The character is redrawn with `TextOut` at the destination cell offset (+10, +3) (Tahoma 19 in the original).
7. If there is no error: the ant moves to the new cell. When the move comes from a program, a black 2-px rectangle, inset 5 px, is drawn in the cell just left; this is the **trail**. Moves made with the on-screen arrow buttons pass "no trail", still change facing and still wait the delay, and clear the error flag afterwards.
8. Always: wait `delay` ms, then cell(X,Y) := `'*'`.

**Push rule summary:** the ant pushes exactly one object by exactly one cell. The move fails at the edge, when pushing would put the object off the grid, and when two objects are adjacent in the direction of movement.

Quirk [O]: if the error flag is **already** set when a move starts, steps 1–5 still run, so a blocked move is still undone. If the move is not blocked, the new position is kept, but the push, the sprite move and the trail are skipped (0x4547be jumps to 0x454b64). Step 8 still writes `'*'` into the new cell, so **an object there is destroyed** without being pushed, and the sprite stays drawn at the old position. This matters inside procedures (§5.7), after Stop (§5.3), and for the first arrow click after a failed run, because the flag is not cleared when a run ends.

### 5.3 Main execution loop [O] `RunButtonClick` @0x459ea0

1. Run the syntax check (0x459ece). It is **not** silent: only C7 ("syntax OK") is suppressed; C8, C1 and the warnings C2–C6 are shown as usual. If it reports an error (an invalid line or unbalanced REPEAT), stop. Because of the uninitialised result flag (§4.3), a valid program can also be refused without a message.
2. Save a snapshot of the grid and the program to `!temp.tmp`, in the file format of §7. Then set cell(ant) := `'*'` (0x459f43), PC := beginLine and error := 0. If `!temp.tmp` already exists, Save asks D27 and then skips writing whatever the answer (0x45911b); Save also leaves the save dialog's file name set to `!temp.tmp`.
3. While `PC ≤ endLine` and there is no error:
   1. Process pending UI events.
   2. `PC := PC + 1`.
   3. `L := Normalize(line[PC])`; `w := NextWord(L)`.
   4. Dispatch:
      - `w` against the moves, as an else-chain in the order LEFT, RIGHT, UP, DOWN (0x459fc9), so extra words after a move are ignored;
      - then, as independent tests: `w == IF` → IF; `w == REPEAT` → REPEAT; `w == WHILE` → WHILE;
      - then **always** a procedure lookup on `w` (first match) → CALL, even if a keyword already ran;
      - anything else (BEGIN, END, end markers, conditions, PROC headers) does nothing.
4. After the loop (0x45a0d7–0x45a1b9):
   - Process pending UI events.
   - **No error**, and BEGIN and END both exist: ask **C10** (confirmation, OK and Cancel).
   - **Error**: show **C11**, then **always** ask C10, with no BEGIN/END test. Then PC := −1.
   - **OK** loads `!temp.tmp` silently (the initial grid, ant and program); the load deletes `!temp.tmp` and clears the open dialog's file name. OK does not call the trail eraser 0x454150; the trail is only overdrawn by the load blanking each cell, which may leave remnants [I].
   - **Cancel** deletes `!temp.tmp` and erases the trail (0x454150: white 2-px rectangles, then objects redrawn).
   - If the syntax check failed, nothing further happens.

If BEGIN is missing (beginLine = −1), execution starts at line 0. [O]

**Off-by-one quirk [O]** (0x45a0bd): the loop condition `PC ≤ endLine` is tested *before* the increment, so **the line immediately after `END` is executed too.**

**Stop [O]** (0x45a904): the Stop button sets the error flag and itself processes UI events. `ProcessMessages` (0x443548) has exactly three callers: the loop head (0x459f65), after the loop (0x45a0de) and the Stop handler (0x45a91e). REPEAT, WHILE, CALL and the moves never process events, so Stop has no effect while they run. The click is delivered at the loop head *after* the loop condition was tested, so **one more main-program line is fetched and executed with the error flag set** (in the quirk mode of §5.2). Stop is then reported as C11, followed by C10.

**Re-entrancy [O]:** the Run and arrow buttons are not disabled during a run. Clicking Run again starts a nested run (whose snapshot hits the existing-`!temp.tmp` path above), and an arrow click clears the error flag.

### 5.4 IF [O] 0x455e6c

Run time sees the rest of the line as `cond THEN instr1 [w5 instr2]`. Neither `THEN` nor `w5` is checked at run time (0x455ec0–0x455ed5); a leading `IF` word is skipped if present (0x455eac). IF does not check the error flag.

Condition truth (as implemented):

| Facing | AT_EDGE is true when | Correct edge |
|---|---|---|
| up | Y = 1 | Y = 1 |
| down | Y = 10 | Y = 10 |
| left | **X = 10** | X = 1 |
| right | **X = 1** | X = 10 |

`NOT_AT_EDGE` is the negation; any other condition word counts as true. If the condition is true, `instr1` runs; otherwise `instr2` runs, if present. A branch is compared with UP, DOWN, RIGHT and LEFT (independent tests) and then always looked up in the procedure table (first match).

**Bug [O]** (disassembly 0x455f45–0x455fe4): for horizontal facing, IF tests the **opposite** edge. WHILE (§5.6) uses the correct edges.

### 5.5 REPEAT [O] 0x456198

1. `n := StrToInt(count word)`. The body starts at PC+1.
2. Repeat `n` times, stopping early on error (checked per line at 0x4563ec and per pass at 0x45640b). Each pass reads lines one by one from the body start; there is no separate scan:
   - `L := Normalize(line)`. If `L == END_REPEAT` (0x4563dc), the pass ends.
   - Otherwise the line is dispatched: `L` against the moves as a whole line (UP, DOWN, RIGHT, LEFT; 0x456269–0x4562cc); then by first word, `IF` → IF (0x4562df) and `WHILE` → WHILE (0x456304); then a procedure lookup by first word (0x45636b).
   - The error flag is set only when the line index exceeds `Lines.Count` (0x45625c); the line at index `Count` reads as empty. The line that sets the error is still dispatched, then the loop exits.
3. Set PC := the `END_REPEAT` line (after an error: the line that failed).

Quirks [O]:
- **A REPEAT directly inside a REPEAT body is not executed.** The `REPEAT` head word is never tested in a REPEAT body, so the inner `REPETA` line is ignored, and the inner `SFIRSIT REPETA` ends the outer body early. PC is left on the inner end marker, so the lines between the inner and outer end markers then run **once more** in the enclosing context, and the outer end marker does nothing. Nesting works through a procedure.
- **n = 0:** the body is skipped, but PC is set to the *first body line* (0x456419), so the caller continues from the *second* body line. The body therefore runs once, minus its first line. This holds in the main program, in a WHILE body and in a procedure body.
- A WHILE inside a REPEAT works: PC is handed over before the call and read back after it (0x456321/0x456330).
- No upper limit apart from a 32-bit integer. [I]

### 5.6 WHILE [O] 0x45644c (disassembly 0x456476–0x4567c8)

- **If the condition is `AT_EDGE`, the body never runs**, whatever the ant's position (0x4564a2–0x4564b3). In fact any condition word other than `NOT_AT_EDGE` skips the body. Execution scans to the end marker and continues there.
- With `NOT_AT_EDGE` it behaves as a **do-while**: the body always runs at least once (0x4564b9).
- Body lines are run in sequence, stopping on error (0x456766):
  - whole-line move (0x456509–0x45656c);
  - first word `IF` → IF (0x45657c);
  - first word `REPEAT` → REPEAT (0x4565a1);
  - a procedure lookup that compares names against the **rest of the line after the first word** (0x45660a). This is a bug: **a procedure call on its own line inside a WHILE body never runs**, because its rest is empty. Conversely, a procedure named like the second word of a line (for example a procedure `CIT`) is called by that line, including on every `SFIRSIT CIT` line.
  - The end line is recognised as first word `END` with rest `WHILE` (0x456626–0x45664f). On it, control jumps back to the body start, and the exit test runs.
  - **A WHILE directly inside a WHILE is not executed:** the `WHILE` head word is never tested. The inner `SFIRSIT CIT` acts as the outer loop's end line.
- The loop ends at an end line when the ant faces the edge (down & Y=10, up & Y=1, left & X=1, right & X=10, which are the correct edges; 0x45665f–0x45675c). So the condition is tested **only at the end of each pass**.
- Afterwards (0x456774–0x4567be), PC := the first line equal to `END_WHILE` at index ≥ body start + 1, i.e. the first `END_WHILE` *after the first body line*. The scan has no bounds check: if there is none, it reads empty lines forever (effectively a hang). So an **empty body** (`CIT … EXECUTA` directly followed by `SFIRSIT CIT`) or a **missing `END_WHILE`** hangs, unless a later `END_WHILE` line exists. After an error, PC is also that `END_WHILE` line, not the line that failed. With nested WHILE, PC lands on the inner end marker, so the lines up to the outer marker run once more in the enclosing context.
- Infinite loops are possible, and Stop cannot interrupt them (§5.3).

### 5.7 Procedure call [O] 0x4567f4

- Save PC (0x456817) and continue from the procedure's header line: the table stores header index + 1, and CALL sets the index to stored − 1 (0x456838–0x456847), i.e. the header itself, which is then skipped by the pre-increment. Lookups take the first match in the table.
- Run the following lines, each dispatched before the end test, until a whole normalised line equals `END_PROC` (0x456a24):
  - whole-line move;
  - first word `IF` → IF;
  - `REPEAT` → REPEAT;
  - `WHILE` → WHILE;
  - procedure name → CALL. **Recursion is allowed and unlimited**; deep recursion overflows the stack.
- Restore PC on return (0x456a3b).
- **The body loop never checks the error flag**, including the error set by running past the last line (0x4568cb). After a failed move, the rest of the procedure keeps running in the quirk mode of §5.2. Inside it, a REPEAT then runs zero passes and leaves PC on its first body line, so the procedure continues from the second body line; a WHILE skips straight to its `END_WHILE` line.
- If `END_PROC` is missing, execution runs on past the procedure text, through `BEGIN` and the main program, in procedure context, and stops at the next line equal to `END_PROC` (for example, the next procedure's end marker). Only if there is none does it hang, reading empty lines until an integer overflow after about 2³¹ lines; a line that calls the same procedure recurses until the stack overflows. [O]

### 5.8 Which statements work in which context [O]

| Context | Moves | IF | REPEAT | WHILE | Call | Stops on error / Stop |
|---|---|---|---|---|---|---|
| Main program | by first word | yes | yes | yes | by first word, always tried | yes (and processes UI events) |
| REPEAT body | whole line | yes | **no** | yes | by first word, always tried | error only |
| WHILE body | whole line | yes | yes | **no** | **broken** (by second word) | error only |
| Procedure body | whole line | yes | yes | yes | by first word, always tried (recursive) | **no** |

### 5.9 Recommended corrected semantics [P]

For a modern reimplementation that keeps the language but drops the bugs:
- Run exactly the lines between BEGIN and END.
- Every statement works in every context, including direct nesting of REPEAT in REPEAT and WHILE in WHILE.
- `WHILE c DO … END_WHILE` is a pre-test loop that runs while `c` is true, for both conditions.
- IF and WHILE test the same, correct edges.
- `REPEAT 0` runs the body zero times.
- An error anywhere stops the whole program.
- Stop works everywhere.
- The procedure table is rebuilt on every check, and procedure names may not equal keywords.
- Every flag is initialised; the checker validates each line exactly once, against the grammar of §4.2.
- Missing end markers (REPEAT, WHILE, procedure) are syntax errors.
- A move never destroys an object.
- Add a configurable step limit to guard against infinite loops.

Offer a **compatibility mode** that reproduces §5.3–§5.8 exactly, so that legacy example programs behave as they did in class.

---

## 6. Limits

| Item | Limit | Evidence |
|---|---|---|
| Grid | 10 × 10 cells | [O] |
| Objects | one character per cell; any byte except empty, space and `*` | [O] 0x4585bc |
| Procedures | table `array[1..256]` of 8-byte entries at 0x45da24; ≤ 256 registrations per session, the 257th raises a range-check error (0x4599f1); see §9 #10 | [O] |
| REPEAT count | 0 .. 2³¹−1 | [O] |
| Recursion | unbounded (until stack overflow) | [O] |
| Line length | lines are read with `EM_GETLINE` into a 4096-byte buffer, so longer lines are truncated | [O] 0x42162c |
| Move delay | 200 − 10·pos ms, slider position 0..20; default 100 ms. The speed dialog opens at pos = 20 − delay/10 (0x456f10); OK stores 200 − 10·pos (0x456ec5–0x456eee), applied when the dialog closes (0x457020); Cancel keeps the delay but resets the slider to delay/10 (cosmetic bug) | [O] 0x45b928 |

---

## 7. File format (`.ant`) [O] save @0x45903c, load @0x458aa4

Plain single-byte text (cp1250 on a Romanian system [I]), CRLF line endings. Open/save filter: `Ant files|*.ant|All files|*.*`.

```
Ant executor file            ← literal, str 0x4593fc
[table description]          ← literal, str 0x459418
<X> <Y>                      ← ant column and row, decimal, one space
<facing>                     ← 1..4 (1 down, 2 left, 3 up, 4 right)
<x> <y> <c>                  ← one line per non-empty cell; rows y = 1..10 (outer loop),
...                            columns x = 1..10 (inner loop); c is the raw cell byte,
                               including '*' for the ant itself
666 666 *                    ← terminator, str 0x459434
<program text>               ← the editor text, verbatim (lines separated by CRLF, no CRLF after the last line)
```

- **Save:** the program is written with `Write(Memo.Text)`, not `WriteLn`, so the file has no final CRLF. If the chosen name exists, a confirmation question is asked (D27, Yes/No) and the file is written only on Yes. Then `.ant` is appended when the 4th-from-last character of the file name is not `.` (0x4593ec). Because the append comes *after* the existence check (and the dialog has no `DefaultExt` or overwrite prompt), saving as `prog` silently overwrites an existing `prog.ant`. A name shorter than 4 characters raises a range-check error.
- **Load:** all 100 cells are cleared and blanked on screen. The first two lines are skipped without validation. Then X and Y are read and the sprite placed, then facing is read and its sprite loaded. The loader reads the first record before its loop and then repeatedly reads `a`, `b`, a separator character and the cell character, until `a = 666` (whatever `b` and `c` are), setting cell(a,b) := c and drawing non-`'*'` characters centred. The editor is cleared and every remaining line is added. Nothing is validated: out-of-range coordinates, a facing outside 1..4, or a missing terminator (reads at end of file give 0) raise a range-check error. Load does not touch the error flag.
- `!temp.tmp` uses the same format and is the snapshot taken before Run; loading it after a run also deletes it (0x458fa8).

Example:
```
Ant executor file
[table description]
1 1
1
1 1 *
3 1 A
666 666 *
INCEPUT
DREAPTA
SFIRSIT
```

---

## 8. Messages

The message **texts** are lines 20–31 of the localisation file and are unknown [U]. Their **roles** are [O]:

| ID | Slot (global) | Shown when | Blocks Run? | Where |
|---|---|---|---|---|
| C1 | 0x45d910 | REPEAT and END_REPEAT counts differ | yes | 0x459d1b |
| C2 | 0x45d914 | BEGIN or END is missing | no (warning) | 0x459d39 |
| C3 | 0x45d918 | more than one BEGIN | no | 0x459d4b |
| C4 | 0x45d91c | more than one END | no | 0x459d5d |
| C5 | 0x45d920 | the program is empty; unreachable in practice, because an empty program has no BEGIN and C2 fires first | no | 0x459d83 |
| C6 | 0x45d924 | END comes before BEGIN | no | 0x459d9c |
| C7 | 0x45d928 | no invalid line (only from the "Analiza sintactica" command) | — | 0x459e2c |
| C8 | 0x45d92c | syntax-error header | yes | 0x459daf |
| C9 | 0x45d930 | the "line" label, also used in the status bar | — | 0x459dba, 0x45a7c5, 0x45a879 |
| C10 | 0x45d934 | after a run: "restore the initial state?" (`MessageDlg` confirmation, OK + Cancel; OK = restore) | — | 0x45a109, 0x45a170 |
| C11 | 0x45d938 | runtime error, also after Stop | — | 0x45a15b |
| C12 | 0x45d93c | exit confirmation (Yes/No; closes only on Yes) | — | 0x45a6f8 |

Priority [O] (0x459cec–0x459e36): the messages form an else-if chain: an invalid line (C8), else unbalanced REPEAT (C1), else the warnings C2–C6 in that order. Separately, C7 is shown whenever no line was invalid and the check came from the "Analiza sintactica" command, so it **also follows C1–C6**, including the blocking C1.

The status bar uses two different prefixes: `Memo1KeyDown` (also wired to OnKeyUp in the DFM) uses the hard-coded `Rindul:`, while `Memo1KeyPress` and `Memo1Enter` use C9. [O]

The syntax-error message is built as follows (0x459daf):
`C8 + CR + C9 + (line number, 1-based) + CR + '"' + original unnormalised line + '"'`.

Hard-coded Romanian strings [O]: `Rindul:` (status-bar prefix, 0x45a338; the DFM default is `Rindul: 0`) and `Chiar doriti ?` (confirmation for "New", 0x4594dc).

Suggested Romanian texts for a reimplementation [P], none of them original:
- C1: `Numarul de REPETA nu corespunde cu numarul de SFIRSIT REPETA`
- C2: `Lipseste INCEPUT sau SFIRSIT`
- C3: `INCEPUT apare de mai multe ori`
- C4: `SFIRSIT apare de mai multe ori`
- C5: `Programul este gol`
- C6: `SFIRSIT apare inainte de INCEPUT`
- C7: `Sintaxa este corecta`
- C8: `Eroare de sintaxa`
- C9: `Rindul: `
- C10: `Restabiliti starea initiala?`
- C11: `Furnica nu poate executa comanda`
- C12: `Doriti sa iesiti?`

---

## 9. Bug and quirk catalogue

Each item says whether a reimplementation should be faithful (**F**) or correct (**C**). The recommendation is [P].

| # | Quirk | Evidence | Recommendation |
|---|---|---|---|
| 1 | The line after `END` is executed. | 5.3, [O] 0x45a0bd | C (F in compatibility mode) |
| 2 | IF tests the opposite edge when facing left or right. | 5.4, [O] 0x455f45 | C |
| 3 | `WHILE AT_EDGE` never runs its body. | 5.6, [O] | C |
| 4 | `WHILE NOT_AT_EDGE` is a do-while (tested after each pass). | 5.6, [O] | C |
| 5 | REPEAT directly inside REPEAT is not executed; the inner end marker ends the outer loop, and the lines up to the outer end marker run once more. | 5.5, [O] | C |
| 6 | WHILE directly inside WHILE is not executed; the inner end marker acts as the outer loop's end, and the lines up to the outer end marker run once more. | 5.6, [O] | C |
| 7 | A procedure call on its own line inside a WHILE body never runs; a line whose *second* word is a procedure name calls it instead. | 5.6, [O] | C |
| 8 | `REPEAT 0` runs the body once, minus its first line. | 5.5, [O] | C |
| 9 | A procedure keeps running after an error. | 5.7, [O] | C |
| 10 | The procedure table is never reset (counter 0x45e22c is only incremented, at 0x4599d3; nothing else writes it). Every Check **and every Run** re-registers all procedures; lookups take the first match, so edited programs can jump to stale header lines, and names from earlier programs still pass the checker. The 257th registration raises a range-check error; from then on every PROC, call or IF line that is checked raises too, until the program restarts. | 4.3, [O] | C |
| 11 | Stop works only between main-program lines, and one more line runs (with the error flag set) after it is clicked. | 5.3, [O] | C |
| 12 | Missing, duplicate or misordered BEGIN/END are only warnings. | 4.5, [O] | C |
| 13 | WHILE and procedure end markers are not balanced by the checker. | 4.3, [O] | C |
| 14 | A failed move still changes facing. | 5.2, [O] | F (harmless and visible) |
| 15 | The IF checker accepts a dangling `ALTFEL`, an unchecked 4th word, and an unchecked else branch when it is the last word; its else-valid flag is uninitialised. | 4.6, [O] | C |
| 16 | A TAB makes a line invalid. | 3.1, [O] | C |
| 17 | A missing `END_PROC` makes the call run on through the following text until some later `END_PROC` line, or hang if there is none. | 5.7, [O] | C (report a syntax error) |
| 18 | Run passes an uninitialised result flag to the syntax check, so a valid program can be refused silently. | 4.3, [O] 0x459ec9 | C |
| 19 | The checker's head-keyword tests share one variable, so lines such as `REPETA 3 DACA E_MARGINE ATUNCI SUS` pass. | 4.3, [O] | C |
| 20 | A procedure named like a keyword runs in addition to it (no shadowing). | 3.3, 5.3, [O] | C (reject keyword names) |
| 21 | An empty WHILE body, or a missing `END_WHILE`, hangs. | 5.6, [O] | C (report a syntax error) |
| 22 | A move made while the error flag is already set destroys an object in the target cell. | 5.2, [O] | C |
| 23 | The error flag is not cleared when a run ends; the next arrow-button move runs in the quirk mode of #22. | 5.1, [O] | C |
| 24 | After an error, C10 is always asked, even when BEGIN or END is missing; OK does not erase the trail. | 5.3, [O] | C |
| 25 | Saving as `name` silently overwrites an existing `name.ant`. | 7, [O] | C |

---

## 10. Editor and UI behaviour relevant to the language

- **Insert buttons** [O] 0x45a968–0x45b350:
  - `INCEPUT` and `SFIRSIT` insert a new line before the caret line.
  - Every other keyword button appends `keyword + ' '` to the caret line.
  - `EXECUTA` appends without the trailing space.
  - `Sfirsit...` appends `SFIRSIT `, so the user then picks the block type.
- **Menu items** [O] (default Romanian captions from the DFM):
  - Fisier (Nou, Citire ..., Salvare ..., separator, Iesire);
  - Program (Analiza sintactica, Executare);
  - Configurare (Viteza, Limbajul: Romana, Rusa, Engleza);
  - Ajutor (Despre, Utilizare).
  - Iesire is wired to `ExitProgramClick`; it and `Iesire1Click` both just call `Close`, so C12 is asked. Toolbar hints are not localised.
- **D slots** [O] (ReadLanguage 0x457f86–0x45815f, speed dialog `FormActivate` 0x456f55–0x456fcd, help window `FormActivate` 0x45729c–0x4572c3, SaveFileClick 0x459108):

  | Slot | Target | Slot | Target | Slot | Target |
  |---|---|---|---|---|---|
  | D1 | Fisier | D11 | Ajutor | D21 | speed dialog OK button |
  | D2 | Citire | D12 | Despre | D22 | speed dialog `Anulare` button |
  | D3 | Salvare | D13 | Utilizare | D23 | help window caption |
  | D4 | Iesire | D14 | GroupBox `Editare:` | D24 | help window Exit button |
  | D5 | Program | D15 | Label `Caracterul:` | D25 | Nou |
  | D6 | Analiza sintactica | D16 | CheckBox `Stergere` | D26 | main window caption |
  | D7 | Executare | D17 | GroupBox `Setare pozitie:` | D27 | **message**: overwrite confirmation (Yes/No) |
  | D8 | Configurare | D18 | speed dialog `Alegeti viteza furnicii:` | D28 | Romana |
  | D9 | Viteza | D19 | speed dialog `Viteza Minima` | D29 | Rusa |
  | D10 | Limbajul | D20 | speed dialog `Viteza Maxima` | D30 | Engleza |

  SpeedButton19 (`Sfirsit...`) gets the caption END + `'...'` at run time (0x4582c4).
- **Grid editing** [O] 0x4585bc:
  - Clicking an empty, non-ant cell places the character typed in the one-character "Caracterul:" box (MaxLength 1). Case is preserved; empty, space and `*` are refused. Any mouse button works.
  - With "Stergere" (delete) checked, the character box and its label are hidden, and a click clears the cell (it may first place the character, but the net effect is a clear). The original does not protect the ant's own cell, so its `'*'` marker can be lost.
  - The arrow buttons "Setare pozitie" move the ant with the pushing rules, change facing, wait the move delay, draw no trail, and clear the error flag.
  - The "Rotire" button cycles the facing 4 → 3 → 2 → 1 → 4 (right → up → left → down, counter-clockwise) and redraws the sprite (0x45a214–0x45a22b).
- **New** asks `Chiar doriti ?` (information icon, Yes/No). Yes clears the grid and calls `FormCreate` again, with the same effects as a language switch (§2.1): the program is cleared, `!temp.tmp` deleted, and the ant put at (1,1) facing down.

---

## 11. Test cases

Each case uses the Romanian keywords and the initial state from §5.1 (ant at (1,1) facing down, empty grid) unless stated otherwise. **Faithful** is the original's behaviour (§5.3–§5.8); **Corrected** is the behaviour from §5.9.

| # | Program / setup | Faithful | Corrected |
|---|---|---|---|
| T1 | `INCEPUT` / `DREAPTA` / `SFIRSIT` | ant at (2,1), trail in (1,1) | same |
| T2 | object `A` at (3,1); `INCEPUT` / `DREAPTA` / `DREAPTA` / `SFIRSIT` | ant (3,1), `A` at (4,1) | same |
| T3 | objects at (2,1) and (3,1); `INCEPUT` / `DREAPTA` / `SFIRSIT` | runtime error C11, then the C10 question; ant stays at (1,1), facing right | same |
| T4 | `INCEPUT` / `SUS` / `SFIRSIT` | wall error C11, then C10 | same |
| T5 | `inceput` / `dreapta` / `sfirsit` (lower case) | same as T1 | same |
| T6 | a line `\tDREAPTA` (tab) | syntax error C8 on that line | accepted (extension) |
| T7 | `DACA E_MARGINE` / `ATUNCI SUS` (two lines) | syntax error on line 1 | syntax error |
| T8 | `INCEPUT` / `REPETA 3 ORI` / `DREAPTA` / `SFIRSIT REPETA` / `SFIRSIT` | ant (4,1) | same |
| T9 | `INCEPUT` / `REPETA 2 ORI` / `REPETA 2 ORI` / `DREAPTA` / `SFIRSIT REPETA` / `SFIRSIT REPETA` / `SFIRSIT` | the inner REPETA is ignored; ant (3,1) | ant (5,1) |
| T10 | `INCEPUT` / `CIT NU_E_MARGINE EXECUTA` / `DREAPTA` / `SFIRSIT CIT` / `SFIRSIT` | ant (10,1) | ant (10,1) |
| T11 | `INCEPUT` / `CIT E_MARGINE EXECUTA` / `SUS` / `SFIRSIT CIT` / `SFIRSIT` with the ant at (1,1) facing up | body skipped, no error | body runs: SUS at the wall gives error C11 |
| T12 | `INCEPUT` / `DREAPTA` / `DACA E_MARGINE ATUNCI SUS ALTFEL JOS` / `SFIRSIT` | facing right at X=2: the faithful test is X=1, false → JOS → ant (2,2) | X=10 is false → JOS → ant (2,2) |
| T13 | ant at (1,1) facing right; `INCEPUT` / `DACA E_MARGINE ATUNCI JOS ALTFEL SUS` / `SFIRSIT` | faithful test X=1 is **true** → JOS → ant (1,2) | X=10 is false → SUS → wall error |
| T14 | `PROCEDURA P` / `DREAPTA` / `SFIRSIT PROCEDURA` / `INCEPUT` / `P` / `P` / `SFIRSIT` | ant (3,1) | same |
| T15 | fresh session; `INCEPUT` / `P` / `SFIRSIT` / `PROCEDURA P` / … | syntax error: P is not yet defined (but accepted if P was registered by an earlier Check or Run in the session, §9 #10) | syntax error |
| T16 | `INCEPUT` / `EXECUTA P` / `SFIRSIT` with P defined | syntax error: there is no call keyword | syntax error |
| T17 | `INCEPUT` / `SFIRSIT` / `DREAPTA` | **DREAPTA runs** (off-by-one) → ant (2,1) | the extra line is a syntax error, or it does not run |
| T18 | `INCEPUT` / `REPETA 0 ORI` / `DREAPTA` / `JOS` / `SFIRSIT REPETA` / `SFIRSIT` | only JOS runs → ant (1,2) | nothing runs |
| T19 | `PROCEDURA P` / `DREAPTA` / `SFIRSIT PROCEDURA` / `INCEPUT` / `CIT NU_E_MARGINE EXECUTA` / `P` / `SFIRSIT CIT` / `SFIRSIT` | P never runs inside the WHILE; with the ant facing down at (1,1), the loop body does nothing, so the loop never ends (hang) | ant moves right to (10,1) |
| T20 | `PROCEDURA SUS` / `DREAPTA` / `SFIRSIT PROCEDURA` / `INCEPUT` / `JOS` / `SUS` / `SFIRSIT` | the `SUS` line moves up *and* calls the procedure → ant (2,1) | the procedure name is rejected |
| T21 | ant at (1,10) facing down; `INCEPUT` / `CIT NU_E_MARGINE EXECUTA` / `SFIRSIT CIT` / `SFIRSIT` | the exit test succeeds at once, but the final scan starts after the `SFIRSIT CIT` line and never finds another → hang | condition false → nothing runs, program ends |
| T22 | "Analiza sintactica" on `INCEPUT` / `REPETA 3 DACA E_MARGINE ATUNCI SUS` / `SFIRSIT REPETA` / `SFIRSIT` | no invalid line, REPEAT balanced → C7 (§4.3 cross-keyword quirk) | syntax error on line 2 |
| T23 | `INCEPUT` / `REPETA 2 ORI` / `DREAPTA` / `REPETA 2 ORI` / `JOS` / `SFIRSIT REPETA` / `DREAPTA` / `SFIRSIT REPETA` / `SFIRSIT` | each outer pass runs DREAPTA, JOS (ant (3,3)); then the lines after the inner end marker run once: DREAPTA → ant (4,3) | ant (5,5) |

---

## 12. Textbook (Grade 8, 2020, chapter 2) compared with the binary

| Textbook says | Binary does |
|---|---|
| Program = procedures, then `ÎNCEPUT … SFÂRŞIT` | Same structure; spelled `INCEPUT` / `SFIRSIT` with no diacritics [I] |
| `PROCEDURA Nume … SFÂRŞITUL PROCEDURII` | `PROCEDURA Nume … SFIRSIT PROCEDURA` [I] |
| Call: `EXECUTĂ Nume` | Bare name on its own line; `EXECUTA P` is a syntax error [O] |
| Commands `SUS JOS DREAPTA STÂNGA`; push "when possible" | `STINGA`; one object, one cell; fails at the edge or with two objects in a row [O] |
| `REPETĂ n ORI … SFÂRŞITUL REPETĂRII`, nesting allowed | `REPETA n ORI … SFIRSIT REPETA`; direct nesting is broken [O] |
| `CÂT cond … SFÂRŞITUL CICLULUI` | `CIT cond EXECUTA … SFIRSIT CIT`; only `NU_E_MARGINE` works, as a do-while [O] |
| `DACĂ cond` / `ATUNCI i1` / `ALTFEL i2` on separate lines | Everything on one line; `ALTFEL` optional; one word per branch [O] |
| Conditions `E_LINIE`, `E_MARGINE`, `NU E_LINIE`, `NU E_MARGINE` | Only `E_MARGINE` and `NU_E_MARGINE` (one token, with underscores). `E_LINIE` and `NU E_LINIE` do not exist in this program [O] |
| A runtime error shows a message and stops | True in the main program and loops; inside a procedure, execution continues [O] |

---

## 13. Open questions

1. The exact contents of `romana.lng`, `rusa.lng` and `engleza.lng`: all keyword spellings, the 12 message texts and D27. Copies may survive on old school computers. [U]
2. The exact spelling of `SFIRSIT CIT`, `SFIRSIT REPETA` and `SFIRSIT PROCEDURA`. These are strongly inferred from the help text and from the constraints in §2.2. [I]
3. ~~What the editor returns for a line index past the end.~~ Resolved: `TMemoStrings.Get` (0x42162c) sends `EM_GETLINE` with no bounds check; for an index past the end Windows copies 0 characters, so the line is the empty string. [O]/[I]
4. ~~The exact argument order of the trail rectangle.~~ Resolved: RIGHT, UP and DOWN pass normalised coordinates; LEFT passes X1 = (X+1)·35−5 and X2 = X·35+5, i.e. swapped (0x45510e–0x455187). GDI normalises them, so the result is the same. [O]
5. What the main window shows after a startup with a missing `.lng` file (§2.1); this needs the program to be run. [I]

---

## 14. How to revalidate this specification

Tools that were used (all on macOS; no Windows needed):
- Ghidra 12.1.4 (Homebrew `ghidra`) with JDK 21. Ghidra's auto-analysis **does not** create functions for Delphi published event handlers. They have to be created at the addresses from the RTTI method table. The script `tools/DumpApp.java` (in this folder) does that and decompiles a range: `analyzeHeadless <proj> <name> -import Furnica.exe -scriptPath tools -postScript DumpApp.java <out.c> 0x455000 0x45ba00 <handler addresses…> -deleteProject`.
- The REA reverse-engineering CLI/MCP (`npx rea-agents`) with the Ghidra provider, for evidence-tracked string searches and decompilation.
- `tools/helpers/` holds the Python helpers: `pe.py` (VA → file offset, Delphi AnsiString reader), `dfm.py` (TPF0 form parser), `vmt.py` (RTTI fields and methods). Set `EXE=/path/to/Furnica.exe` before running them.
- `evidence/` holds the parsed forms (`mainform.txt`, `contents.txt` = help text, `okdlg.txt`, `about.txt`).

Published event-handler addresses (from the RTTI method table) [O]:

```
ReadLanguage 0x457d70   SetLanguage 0x4583b4   FormCreate 0x45a3c0
CheckButtonClick 0x459e84 (syntax check)   RunButtonClick 0x459ea0 (run)
OpenFileClick 0x458aa4  SaveFileClick 0x45903c  NewFileClick 0x459440
Up/Down/Left/RightButtonClick 0x45a380/0x45a3a0/0x45a360/0x45a340
StopButtonClick 0x45a904  SpeedButton2Click 0x45a8e4  SpeedButton11Click 0x45a208 (rotate sprite)
SpeedButton1,3..10,12..19Click 0x45a968 0x45a99c 0x45a9d0 0x45aa80 0x45ab30 0x45abe0 0x45ac90 0x45ad40 0x45adf0 0x45aea0 0x45af50 0x45afe0 0x45b090 0x45b140 0x45b1f0 0x45b2a0 0x45b350
Memo1KeyDown 0x45a274  Memo1KeyPress 0x45a750  Memo1Enter 0x45a808  Image1MouseDown 0x4585bc
Romana1/Rusa1/Engleza1Click 0x45b400/0x45b4f4/0x45b5e8   FormCloseQuery 0x45a6f8
```

Internal routines [O]:

```
Normalize 0x4543a4  NextWord 0x454508  SyntaxCheck 0x459b1c  CheckRepeat 0x459508
CheckIf 0x45958c  CheckWhile 0x4597e4  CheckBalance 0x459868  CheckProc 0x45997c
CheckCall 0x459a68  IF 0x455e6c  REPEAT 0x456198  WHILE 0x45644c  CALL 0x4567f4
Move right/left/up/down 0x4545cc/0x454bf4/0x45521c/0x455844  erase trail 0x454150
```

Suggested revalidation order:
1. Confirm the keyword slots and roles in §2.2 from `ReadLanguage` and the dispatch code.
2. Confirm normalisation (§3.1).
3. Check each quirk in §9.
4. Run the test cases in §11 against a reimplementation in both modes.
