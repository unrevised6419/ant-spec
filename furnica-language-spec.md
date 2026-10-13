# Furnica (the Ant executor): language and runtime specification

Version 1.0 · 2026-10-13 · reverse-engineered from the original Windows program

This document describes the programming language of **Furnica** ("Executantul ANT", window caption `Executantul "ANT"`, About box `Ant v2.00`). It was written so that the language can be reimplemented, for example as a web app, and so that every claim can be checked again against the original binary.

School textbooks describe this language together with other teaching executors and simplify it; where the textbook and this program disagree, this document follows the program.

---

## 0. How to read this document

### 0.1 Source of truth

| Artifact | Identity |
|---|---|
| `Furnica.exe` | 557,568 bytes, SHA-256 `cdf5378c1fb1ce45d641a8cdae5ac19b3371a7389ee76c6135e67b2e0fe2e6b2`, file date 2000-01-19 |
| Format | PE32, Intel 80386, Windows GUI, Borland Delphi (VCL), image base `0x400000`, `CODE` section at VA `0x401000` |

Everything here comes from that binary: Ghidra 12.1.4 decompilation, raw disassembly, the Delphi form resources (DFM, binary `TPF0` format) and the RTTI method tables. The program was never executed, so all runtime behaviour is derived from static analysis.

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

The language is selected by `language.cfg`. Its first line is `ROM`, `RUS` or `ENG`, which maps to `romana.lng`, `rusa.lng` or `engleza.lng`. [O] `SetLanguage` @0x4583b4, str 0x458548–0x458594.

If `language.cfg` or the chosen `.lng` file is missing, the original shows an empty message box and closes. [O] So the shipped zip on its own cannot run.

Switching language from the menu reloads the file, **clears the program and the grid**, and puts the ant back at (1,1). [O] 0x45b400 / 0x45b4f4 / 0x45b5e8.

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
- `END_WHILE` must equal `END` + one space + `WHILE`, because the WHILE executor tests for that two-word form.
- Conditions are single words (no space), because they are read with the next-word function (§3.2).
- The original compares keywords exactly as stored, without upper-casing them (§3.1), so every keyword must be written in **upper-case ASCII**.

**There is no call keyword.** A procedure is called by writing its bare name on a line. `EXECUTA` belongs only to the WHILE header (`CIT … EXECUTA`). [O] 0x459a68; the help text says so explicitly (§2.3).

### 2.3 Why the Romanian spellings are trusted

At startup, `ReadLanguage` overwrites the captions of 17 keyword-insert buttons (SpeedButton1–19) with the values from the `.lng` file. Their **design-time** captions, stored in the DFM resource `TMAINFORM`, are therefore the Romanian defaults [O]:
`Inceput`, `Sfirsit`, `Stinga`, `Dreapta`, `Sus`, `Jos`, `Cit`, `Daca`, `E_margine`, `Nu_e_margine`, `Executa`, `Atunci`, `Altfel`, `Repeta`, `Ori`, `Procedura`, plus `Sfirsit...`.

The built-in Romanian help text (DFM `TCONTENTSFORM.Memo1`; it is not localised) uses exactly the upper-case forms in §2.2. Verbatim, in the original spelling (no diacritics; `SFIRSIT` and `STINGA` with *i*):

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
4. One trailing space is removed.

Keywords from the localisation file are compared **as stored** with an exact byte comparison (`LStrCmp` 0x403c64).

Consequences:
- Source text is case-insensitive for ASCII letters: `sus`, `Sus` and `SUS` are the same. [O]
- **Only the space character 0x20 is whitespace.** A TAB is an ordinary character, so a line indented with a tab does not match and is a **syntax error**. [O]/[I]
- Letters with diacritics are neither upper-cased nor folded. [O]

### 3.2 Words [O] `NextWord` @0x454508

`NextWord(line)` returns the characters up to the first space (or the end of the line), removes them from the line, and then removes one more character (the space). Called repeatedly, it yields successive words.

### 3.3 Tokens and other lexical facts

| Item | Rule | Evidence |
|---|---|---|
| Statement separator | The line break. Exactly one statement per line. | [O] 0x459b1c |
| Blank lines | A line that is empty after normalisation is allowed anywhere. | [O] 0x459c24 |
| Comments | **None.** Every non-blank line must be a valid statement or marker. | [O] 0x459b1c |
| Integer (REPEAT count) | Checked with Delphi `Val` (0x4029e0): the parse code must be 0 and the value ≥ 0. At run time it is read with `StrToInt` (0x407c18). `Val` also accepts a leading `+` and `$hex`. | [O]/[I] |
| Procedure name | Any run of non-space characters. Nothing checks for letters or digits, so diacritics, `_` and punctuation are all accepted, compared after ASCII upper-casing. The help text *recommends* letters and digits only. | [O] 0x45997c, 0x459a68 |
| Reserved words | None formally. Keywords take priority only because they are tested first, so a procedure *can* be named like a keyword and will be shadowed. | [O]/[I] |

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

The check runs line by line, from line 0, and **stops at the first invalid line**:
1. `L = Normalize(line i)`.
2. If `L == BEGIN`, record `beginLine = i` and increment `nBegin`. If `L == END`, record `endLine = i` and increment `nEnd`.
3. The line is valid if `L` is empty or equals any of the A-slot keywords (A1–A11) as a whole line.
4. Otherwise `w = NextWord(L)`:
   - `w == REPEAT`: `CheckRepeat` (0x459508). The next word must parse as an integer ≥ 0, and the word after that must be `TIMES`. The rest of the line is ignored.
   - `w == IF`: `CheckIf` (0x45958c), see §4.6.
   - `w == WHILE`: `CheckWhile` (0x4597e4). The next word must be `AT_EDGE` or `NOT_AT_EDGE`, and the word after that must be `DO`. The rest of the line is ignored.
   - `w == PROC`: `CheckProc` (0x45997c). The rest of the line must be exactly one word, the name. The procedure is then **registered** in the procedure table (0x45da24 + 8·(k−1): name, header line = i+1).
5. If the line is still invalid: `CheckCall` (0x459a68) accepts it if the whole line equals a registered procedure name.

After the loop, `CheckBalance` (0x459868) counts the lines whose first word is `REPEAT` and the lines that are `END REPEAT`. If the counts differ, the program is flagged unbalanced. **Only REPEAT blocks are balanced.** Missing WHILE or procedure end markers are not detected by the checker. [O]

### 4.4 Ordering rules
- A procedure must be **defined above** any line that calls it, because calls are validated against the procedures registered so far. [O]
- The help text says procedures go before `BEGIN` [O], but the checker only enforces define-before-use. [O]
- Procedures cannot be nested in each other's text (there is no nesting scan), but a procedure body may call other procedures. [O]

### 4.5 What the original accepts beyond the grammar [O]
- A lone `END_WHILE`, `END_REPEAT`, `END_PROC`, `AT_EDGE` or `NOT_AT_EDGE` line, anywhere. At run time it does nothing.
- Procedure definitions anywhere, even after `END`.
- `BEGIN` and `END` lines counted anywhere in the file. Missing, duplicate or out-of-order markers only produce *warnings* (§8, C2–C6), which do not stop Run.
- Extra words after `REPEAT n TIMES` and after `WHILE cond DO`.

**[P]** A reimplementation should reject all of these, or warn and continue in a clearly labelled compatibility mode.

### 4.6 The IF line in detail [O] `CheckIf` @0x45958c

`L` is the rest of the line after `IF`.
1. `cond = NextWord`; it must be `AT_EDGE` or `NOT_AT_EDGE`.
2. `NextWord` must be `THEN`.
3. `instr1 = NextWord`. It is valid if it is an A-slot keyword or a registered procedure name.
4. If words remain: `w5 = NextWord`. If words still remain: `instr2 = NextWord`, which is valid if it is an A-slot keyword or a procedure name. If no words remain at that point, the else part counts as valid.
5. The line is invalid unless both branches are valid. `w5` must equal `ELSE` **only if** more words remain after `instr2`.

Observed consequences:
- `ELSE` is optional.
- `DACA E_MARGINE ATUNCI SUS ALTFEL` (ELSE with no branch) is accepted.
- `DACA E_MARGINE ATUNCI SUS JOS DREAPTA` is accepted: `w5 = JOS` is not checked, and `DREAPTA` runs as the else branch.
- Words after `ALTFEL x` are ignored.
- Each branch is **exactly one word**: a move or a procedure name. A branch can also be any other A-slot keyword (such as `INCEPUT`), which is accepted but does nothing at run time.
- **The whole IF must be on one line.** A line that starts with `ATUNCI` or `ALTFEL` is invalid.
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
| Error / stop flag | 0x45e240 | set by failed moves, Stop and missing end markers |
| Program counter | 0x45e248 | editor line index |
| Move delay | 0x45d9b8 | milliseconds; 100 by default |

Initial state [O] `FormCreate` @0x45a3c0:
- The ant is at **(1,1)**, the top-left cell, facing **down** (1).
- The grid is empty apart from `'*'` at (1,1).
- The editor is empty.
- A leftover `!temp.tmp` is deleted.

Cells are 35 px in the original UI (`Image1MouseDown`: cell = (x div 35 + 1, y div 35 + 1)). [O]

### 5.2 Moves [O] LEFT 0x454bf4 / RIGHT 0x4545cc / UP 0x45521c / DOWN 0x455844

Described for RIGHT; the other three are symmetric (LEFT: X−1, wall at X<1; UP: Y−1, wall at Y<1; DOWN: Y+1, wall at Y>10).
1. Set facing := right (4) and update the sprite. **Facing changes even if the move then fails.**
2. cell(X,Y) := 0; X := X+1.
3. If X > 10 → **error** (wall), X := X−1.
4. Else, if X < 10 and cell(X,Y) ≠ 0 and cell(X+1,Y) ≠ 0 → **error** (two objects in a row cannot be pushed), X := X−1.
5. Else, if X = 10 and cell(X,Y) ≠ 0 → **error** (an object cannot be pushed off the grid), X := X−1.
6. If there is no error and cell(X,Y) ≠ 0 → **push**: cell(X+1,Y) := cell(X,Y), cell(X,Y) := 0. The character is redrawn (Tahoma 19 in the original).
7. If there is no error: the ant moves to the new cell. When the move comes from a program, a black 2-px rectangle, inset 5 px, is drawn in the cell just left; this is the **trail**. Moves made with the on-screen arrow buttons draw no trail and clear the error flag afterwards.
8. Always: wait `delay` ms, then cell(X,Y) := `'*'`.

**Push rule summary:** the ant pushes exactly one object by exactly one cell. The move fails at the edge, when pushing would put the object off the grid, and when two objects are adjacent in the direction of movement.

Quirk [O]/[I]: if the error flag is **already** set when a move starts, step 2 still runs and the position change is kept, but nothing is redrawn. This matters inside procedures (§5.7).

### 5.3 Main execution loop [O] `RunButtonClick` @0x459ea0

1. Run the syntax check silently. If it reports an error (an invalid line or unbalanced REPEAT), stop.
2. Save a snapshot of the grid and the program to `!temp.tmp`, in the file format of §7. Then set cell(ant) := `'*'`, PC := beginLine and error := 0.
3. While `PC ≤ endLine` and there is no error:
   1. Process pending UI events.
   2. `PC := PC + 1`.
   3. `L := Normalize(line[PC])`; `w := NextWord(L)`.
   4. Dispatch on the first word `w`:
      - a move keyword → move;
      - `IF` → IF;
      - `REPEAT` → REPEAT;
      - `WHILE` → WHILE;
      - a registered procedure name (first match) → CALL;
      - anything else (BEGIN, END, end markers, conditions, PROC headers) → do nothing.
4. After the loop:
   - If there was an error, show **C11** (runtime error).
   - Then, if BEGIN and END both exist, ask **C10** with OK and Cancel buttons. **OK** restores the snapshot (the initial grid, ant and program). **Cancel** deletes the snapshot and erases the trail.

**Off-by-one quirk [O]** (0x45a0bd): the loop condition `PC ≤ endLine` is tested *before* the increment, so **the line immediately after `END` is executed too.**

**Stop [O]** (0x45a904): the Stop button sets the error flag. UI events are processed **only** in the main loop, so Stop has no effect while a REPEAT, WHILE or procedure call is running. It takes effect when control returns to the main loop.

### 5.4 IF [O] 0x455e6c

Run time sees the rest of the line as `cond THEN instr1 [w5 instr2]`. The word `w5` is not checked at run time.

Condition truth (as implemented):

| Facing | AT_EDGE is true when | Correct edge |
|---|---|---|
| up | Y = 1 | Y = 1 |
| down | Y = 10 | Y = 10 |
| left | **X = 10** | X = 1 |
| right | **X = 1** | X = 10 |

`NOT_AT_EDGE` is the negation. If the condition is true, `instr1` runs; otherwise `instr2` runs, if present. A branch is a move or a procedure call.

**Bug [O]** (disassembly 0x455f45–0x455fe4): for horizontal facing, IF tests the **opposite** edge. WHILE (§5.6) uses the correct edges.

### 5.5 REPEAT [O] 0x456198

1. `n := StrToInt(count word)`. The body starts at PC+1.
2. Repeat `n` times, stopping early on error:
   - Scan forward from the body start to the first line equal to `END_REPEAT`. If the scan runs past the last line → error.
   - Run each body line `L` (the whole normalised line):
     - `L` is a move keyword → move;
     - otherwise, by first word: `IF` → IF, `WHILE` → WHILE, procedure name → CALL.
3. Set PC := the `END_REPEAT` line.

Quirks [O]:
- **A REPEAT directly inside a REPEAT body is not executed.** The inner `REPETA` line is ignored, and the inner `SFIRSIT REPETA` ends the outer body early. Nesting works through a procedure. (Only the IF and WHILE heads are tested at 0x4562df / 0x456304.)
- **n = 0:** the body is skipped, but PC is set to the *first body line*, so the main loop continues from the *second* body line. The body therefore runs once, minus its first line.
- No upper limit apart from a 32-bit integer. [I]

### 5.6 WHILE [O] 0x45644c (disassembly 0x456476–0x4567c8)

- **If the condition is `AT_EDGE`, the body never runs**, whatever the ant's position. Execution scans to the end marker and continues there.
- With `NOT_AT_EDGE` it behaves as a **do-while**: the body always runs at least once.
- Body lines are run in sequence:
  - whole-line move;
  - first word `IF` → IF;
  - first word `REPEAT` → REPEAT;
  - a procedure lookup that compares names against the **rest of the line after the first word**. This is a bug: **a procedure call on its own line inside a WHILE body never runs.**
  - **A WHILE directly inside a WHILE is not executed.**
  - When the `END_WHILE` line is reached, control jumps back to the body start.
- The loop ends at an `END_WHILE` line when the ant faces the edge (down & Y=10, up & Y=1, left & X=1, right & X=10, which are the correct edges). So the condition is tested **only at the end of each pass**.
- Afterwards, PC := the first `END_WHILE` line after the body start.
- Infinite loops are possible, and Stop cannot interrupt them (§5.3).

### 5.7 Procedure call [O] 0x4567f4

- Save PC and continue from the procedure's header line.
- Run the following lines until a line equals `END_PROC`:
  - whole-line move;
  - first word `IF` → IF;
  - `REPEAT` → REPEAT;
  - `WHILE` → WHILE;
  - procedure name → CALL. **Recursion is allowed and unlimited**; deep recursion overflows the stack.
- Restore PC on return.
- **The body loop never checks the error flag.** After a failed move, the rest of the procedure keeps running, and because of the quirk in §5.2 the position can become inconsistent.
- If `END_PROC` is missing, the loop never ends. [O]/[I]

### 5.8 Which statements work in which context [O]

| Context | Moves | IF | REPEAT | WHILE | Call | Stops on error / Stop |
|---|---|---|---|---|---|---|
| Main program | by first word | yes | yes | yes | by first word | yes (and processes UI events) |
| REPEAT body | whole line | yes | **no** | yes | by first word | error only |
| WHILE body | whole line | yes | yes | **no** | **broken** | error only |
| Procedure body | whole line | yes | yes | yes | yes (recursive) | **no** |

### 5.9 Recommended corrected semantics [P]

For a modern reimplementation that keeps the language but drops the bugs:
- Run exactly the lines between BEGIN and END.
- Every statement works in every context, including direct nesting of REPEAT in REPEAT and WHILE in WHILE.
- `WHILE c DO … END_WHILE` is a pre-test loop that runs while `c` is true, for both conditions.
- IF and WHILE test the same, correct edges.
- `REPEAT 0` runs the body zero times.
- An error anywhere stops the whole program.
- Stop works everywhere.
- The procedure table is rebuilt on every check.
- Add a configurable step limit to guard against infinite loops.

Offer a **compatibility mode** that reproduces §5.3–§5.8 exactly, so that legacy example programs behave as they did in class.

---

## 6. Limits

| Item | Limit | Evidence |
|---|---|---|
| Grid | 10 × 10 cells | [O] |
| Objects | one character per cell; any byte except empty, space and `*` | [O] 0x4585bc |
| Procedures | ≤ 256 registrations per session; see the bug in §9 | [O] |
| REPEAT count | 0 .. 2³¹−1 | [O]/[I] |
| Recursion | unbounded (until stack overflow) | [O] |
| Move delay | 200 − 10·pos ms, slider position 0..20; default 100 ms | [O] 0x456eb0, 0x456f04, 0x45b918 |

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
<program text>               ← the editor lines, verbatim, each ending in CRLF
```

- **Save:** `.ant` is appended when the 4th-from-last character of the file name is not `.` (0x4593ec). Overwriting an existing file asks a confirmation question (D27, Yes/No).
- **Load:** the first two lines are skipped without validation. Then X, Y and facing are read. The loader repeatedly reads `a`, `b`, a separator character and the cell character, until `a = 666`, setting cell(a,b) := c. The editor is cleared and every remaining line is added.
- `!temp.tmp` uses the same format and is the snapshot taken before Run.

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
| C5 | 0x45d920 | the program is empty | no | 0x459d83 |
| C6 | 0x45d924 | END comes before BEGIN | no | 0x459d9c |
| C7 | 0x45d928 | syntax OK (only from the "Analiza sintactica" command) | — | 0x459e2c |
| C8 | 0x45d92c | syntax-error header | yes | 0x459daf |
| C9 | 0x45d930 | the "line" label, also used in the status bar | — | 0x459dba, 0x45a750, 0x45a808 |
| C10 | 0x45d934 | after a run: "restore the initial state?" (OK = restore) | — | 0x45a0d7, 0x45a152 |
| C11 | 0x45d938 | runtime error (refusal) | — | 0x45a152 |
| C12 | 0x45d93c | exit confirmation | — | 0x45a6f8 |

Priority [O] (0x459cec–0x459e36): an invalid line comes first, then unbalanced REPEAT, then the warnings C2–C6 in that order, then C7.

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
| 5 | REPEAT directly inside REPEAT is not executed, and the inner end marker ends the outer loop. | 5.5, [O] | C |
| 6 | WHILE directly inside WHILE is not executed. | 5.6, [O] | C |
| 7 | A procedure call on its own line inside a WHILE body never runs. | 5.6, [O] | C |
| 8 | `REPEAT 0` runs the body once, minus its first line. | 5.5, [O] | C |
| 9 | A procedure keeps running after an error. | 5.7, [O] | C |
| 10 | The procedure table is never reset (counter 0x45e22c is only incremented, at 0x4599d3). Re-checking duplicates entries; lookups take the first match, so edited programs can jump to stale header lines; after 256 registrations in total, Delphi raises a range-check error. | 4.3, [O] | C |
| 11 | Stop works only between main-program lines. | 5.3, [O] | C |
| 12 | Missing, duplicate or misordered BEGIN/END are only warnings. | 4.5, [O] | C |
| 13 | WHILE and procedure end markers are not balanced by the checker. | 4.3, [O] | C |
| 14 | A failed move still changes facing. | 5.2, [O] | F (harmless and visible) |
| 15 | The IF checker accepts a dangling `ALTFEL` and an unchecked 4th word. | 4.6, [O] | C |
| 16 | A TAB makes a line invalid. | 3.1, [O] | C |
| 17 | A missing `END_PROC` hangs the program. | 5.7, [O]/[I] | C (report a syntax error) |

---

## 10. Editor and UI behaviour relevant to the language

- **Insert buttons** [O] 0x45a968–0x45b350:
  - `INCEPUT` and `SFIRSIT` insert a new line before the caret line.
  - Every other keyword button appends `keyword + ' '` to the caret line.
  - `EXECUTA` appends without the trailing space.
  - `Sfirsit...` appends `SFIRSIT `, so the user then picks the block type.
- **Menu items** [O] (default Romanian captions, slots D1–D30):
  - Fisier (Nou, Citire…, Salvare…, Iesire);
  - Program (Analiza sintactica, Executare);
  - Configurare (Viteza, Limbajul: Romana, Rusa, Engleza);
  - Ajutor (Utilizare, Despre).
- **Grid editing** [O] 0x4585bc:
  - Clicking an empty, non-ant cell places the character typed in the one-character "Caracterul:" box. Case is preserved; empty, space and `*` are refused.
  - With "Stergere" (delete) checked, a click clears the cell. The original does not protect the ant's own cell.
  - The arrow buttons "Setare pozitie" move the ant with the pushing rules and draw no trail.
  - The "Rotire" button only cycles the facing (4 → 3 → 2 → 1 → 4).
- **New** asks `Chiar doriti ?`. Yes clears the grid and the program and puts the ant at (1,1).

---

## 11. Test cases

Each case uses the Romanian keywords and the initial state from §5.1 (ant at (1,1) facing down, empty grid) unless stated otherwise. **Faithful** is the original's behaviour (§5.3–§5.8); **Corrected** is the behaviour from §5.9.

| # | Program / setup | Faithful | Corrected |
|---|---|---|---|
| T1 | `INCEPUT` / `DREAPTA` / `SFIRSIT` | ant at (2,1), trail in (1,1) | same |
| T2 | object `A` at (3,1); `INCEPUT` / `DREAPTA` / `DREAPTA` / `SFIRSIT` | ant (3,1), `A` at (4,1) | same |
| T3 | objects at (2,1) and (3,1); `INCEPUT` / `DREAPTA` / `SFIRSIT` | runtime error C11; ant stays at (1,1), facing right | same |
| T4 | `INCEPUT` / `SUS` / `SFIRSIT` | wall error C11 | same |
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
| T15 | `INCEPUT` / `P` / `SFIRSIT` / `PROCEDURA P` / … | syntax error: P is not yet defined | syntax error |
| T16 | `INCEPUT` / `EXECUTA P` / `SFIRSIT` with P defined | syntax error: there is no call keyword | syntax error |
| T17 | `INCEPUT` / `SFIRSIT` / `DREAPTA` | **DREAPTA runs** (off-by-one) → ant (2,1) | the extra line is a syntax error, or it does not run |
| T18 | `INCEPUT` / `REPETA 0 ORI` / `DREAPTA` / `JOS` / `SFIRSIT REPETA` / `SFIRSIT` | only JOS runs → ant (1,2) | nothing runs |
| T19 | `PROCEDURA P` / `DREAPTA` / `SFIRSIT PROCEDURA` / `INCEPUT` / `CIT NU_E_MARGINE EXECUTA` / `P` / `SFIRSIT CIT` / `SFIRSIT` | P never runs inside the WHILE; with the ant facing down at (1,1), the loop body does nothing, so the loop never ends (hang) | ant moves right to (10,1) |

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
3. What the editor returns for a line index past the end (assumed: an empty string). [I]
4. The exact argument order of the trail rectangle; the visual result is the same either way. [I]

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
