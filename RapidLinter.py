import re
import threading

# --- 1. SETUP ---
LINT_VERSION = str(0.1)
LINT_INDICATOR = 12 # Scintilla has 32 indicator slots. 8 is usually completely safe/unused.
ERROR_STYLE = 200
errors = []
print("RAPIDLINTER V{} LAUNCHED".format(LINT_VERSION))

# --- 2. THE LINTING LOGIC ---
def run_linter():
    text = editor.getText() # Grab file's text
    lines = text.splitlines() # Split into lines
    open_procs = []
    module_present = [False, None, None]
    set_styles()
    print("CHECKING LINES")
    # Safety check: Only run this on ABB RAPID files
    filename = notepad.getCurrentFilename().lower()
    if not filename.endswith(('.mod', '.prg', '.sys')):
        return

    for line_num, line in enumerate(lines):
        clean_line = line.strip().split('!')[0] # Ignore comments
        if not clean_line:
            continue

        keywords = ['FUNC', 'ENDFUNC', 'PROC', 'ENDPROC', 'MODULE', 'ENDMODULE', 'IF', 'ELSEIF', 'ELSE', 'ENDIF', 'WHILE', 'ENDWHILE', 'FOR', 'ENDFOR', 'TRAP', 'ENDTRAP', 'TEST', 'CASE', 'DEFAULT', 'ENDTEST', 'VAR', 'PERS', 'CONST', 'ERROR']
        first_word = clean_line.split()[0].upper() if clean_line else ""

        # Check A: Missing Semicolon
        if not clean_line.endswith(';') and first_word not in keywords and not clean_line.endswith(':'):
            draw_squiggle(line_num, line)

        # Check B: Open and Close FUNC PROC MODULE check
        open_pattern = r'^\s*(FUNC|PROC|ENDFUNC|ENDPROC|MODULE|ENDMODULE)(\s+.*)?'
        proc_match = re.match(open_pattern, clean_line, re.IGNORECASE)
        if proc_match:
            if open_procs:
                if proc_match.group(1) in ('FUNC', 'PROC'):
                    draw_squiggle(open_procs[-1][1], open_procs[-1][2])
                    draw_squiggle(line_num, line)
                    annotate_errors(line_num, "ERROR: {} Opened Before Prev {} Closed: Line# {}-{}".format(proc_match.group(1), open_procs[-1][0], open_procs[-1][1]+1, line_num+1))
                    open_procs.pop()
                    open_procs.append((proc_match.group(1), line_num, line))
                elif proc_match.group(1) in ('ENDFUNC', 'ENDPROC'):
                    if open_procs[-1][0] == proc_match.group(1)[3:len(proc_match.group(1))]:
                        open_procs.pop()
                    else:
                        draw_squiggle(open_procs[-1][1], open_procs[-1][2])
                        draw_squiggle(line_num, line)
                        annotate_errors(line_num, "ERROR: {} Should be Ended with END{}".format(open_procs[-1][0], open_procs[-1][0]))
                        open_procs.pop()
                elif proc_match.group(1) == 'MODULE':
                    if module_present[0] == False:
                        module_present[0] = True
                        endmodule_err = find_endmodule(text)
                    else:
                        print("MODULE ERROR")
                        draw_squiggle(line_num, line)
                        annotate_errors(line_num, "ERROR: Only 1 MODULE allowed per file")
                elif proc_match.group(1) == 'ENDMODULE':
                    if endmodule_err[0] == 1:
                        draw_squiggle(line_num, line, len(endmodule_err[1]))
                        start_pos = (len(line)-len(line.lstrip()))+len(endmodule_err[1])
                        carrot_pos = start_pos*' ' + '^'
                        if len(carrot_pos) > 3: carrot_pos = carrot_pos[3:]
                        annotate_errors(line_num, carrot_pos)
                        annotate_errors(line_num, 'ERROR: "!" Should be the First Character After ENDMODULE')
            else:
                if proc_match.group(1) in ('ENDFUNC', 'ENDPROC'):
                    suffix = proc_match.group(1)[3:]
                    draw_squiggle(line_num, line)
                    annotate_errors(line_num, "ERROR: {} Ended Before {} Was Ever Opened".format(suffix, suffix))
                elif proc_match.group(1) == "MODULE":
                    if module_present[0] == False: 
                        module_present[0] = True
                        endmodule_err = find_endmodule(text)
                    else: 
                        print("MODULE ERROR")
                        draw_squiggle(line_num, line)
                        annotate_errors(line_num, "ERROR: Only 1 MODULE allowed per file")
                elif proc_match.group(1) == 'ENDMODULE':
                    if endmodule_err[0] == 1:
                        draw_squiggle(line_num, line, len(endmodule_err[1]))
                        start_pos = (len(line)-len(line.lstrip()))+len(endmodule_err[1])
                        carrot_pos = start_pos*' ' + '^'
                        if len(carrot_pos) > 3: carrot_pos = carrot_pos[3:]
                        annotate_errors(line_num, carrot_pos)
                        annotate_errors(line_num-1, 'ERROR: "!" Should be the First Character After ENDMODULE')
                else: open_procs.append((proc_match.group(1), line_num, line))

# --- 3. THE DRAWING FUNCTION ---
def draw_squiggle(line_num, line_text, err_gap=0):
    # Scintilla doesn't draw by line number; it needs absolute character indexes.
    start_pos = editor.positionFromLine(line_num)
    
    # Math to skip the tabs/spaces so the squiggle is exactly under the text
    leading_spaces = len(line_text) - len(line_text.lstrip())
    start_pos = start_pos + leading_spaces + err_gap
    length = len(line_text.strip())-err_gap
    if length > 0:
        editor.setIndicatorCurrent(LINT_INDICATOR)
        editor.indicatorFillRange(start_pos, length)

# --- 4. ANNOTATION FUNCTION ---
def annotate_errors(line_num, error_text):
    editor.annotationSetVisible(ANNOTATIONVISIBLE.BOXED)

    editor.annotationSetText(line_num, error_text)
    editor.annotationSetStyle(line_num, ERROR_STYLE)

# --- 5. SET STYLES FUNCTION ---
def set_styles():
    editor.annotationClearAll()
    # --- ENFORCE SQUIGGLE STYLE HERE ---
    editor.indicSetStyle(LINT_INDICATOR, INDICATORSTYLE.SQUIGGLEPIXMAP) 
    
    # Set the color to Red
    editor.indicSetFore(LINT_INDICATOR, (255, 0, 0)) 
    
    # Force BOTH fill and outline to be fully opaque
    editor.indicSetAlpha(LINT_INDICATOR, 255)        
    editor.indicSetOutlineAlpha(LINT_INDICATOR, 255) 
    
    # Draw beneath the text so it doesn't cross out your code
    editor.indicSetUnder(LINT_INDICATOR, True)       
    # -----------------------------------

    # Clear all existing squiggles before we do a fresh pass
    editor.setIndicatorCurrent(LINT_INDICATOR)
    editor.indicatorClearRange(0, editor.getTextLength())

    # Set Error Annotation Style
    editor.styleSetFore(ERROR_STYLE, (255, 255, 255))
    editor.styleSetBack(ERROR_STYLE, (255, 0, 0))
    editor.styleSetBold(ERROR_STYLE, True)

# --- 6. TIMER ---
lint_timer = None

def find_endmodule(text): # -> (int, None/str/tuple, None/str)
    # Index 0 is the error mode. Index 1 and 2 are syntax error strings or line locations
    # Returning 0 means the module is ended correctly!
    # Returning 1 means the module has a syntax error!
    # Returning 2 means no ENDMODULE recognized!
    # Returning 3 means multiple ENDMODULEs recognized!

    # Setup patterns and find every instance of ENDMODULE
    pattern = r'^\s*ENDMODULE.*$'
    strict_pattern = r'^\s*?ENDMODULE(?:\s*!.*)?\s*$'
    garbage_pattern = r'^(?P<endmodule>.*?ENDMODULE\s*)(?P<garbage>[^!].*?)$'
    matches = list(re.finditer(pattern, text, re.MULTILINE))

    
    if not matches: # If no matches, return no error 2
        return (2, None, None) # ENDMODULE does not exist
    
    if len(matches) > 1: # If multiple ENDMODULE lines, return error 3
        if len(matches) > 1:
            return(3, None, None) # Maybe add tuple for duplicate ENDMODULE locations
    
    last_endmodule_line = matches[-1].group(0).strip()

    if re.search(strict_pattern, last_endmodule_line):
        return (0, None, None) # Perfect
    else:
        syntax_err_pos = re.search(garbage_pattern, last_endmodule_line)
        if syntax_err_pos:
            return (1, syntax_err_pos.group('endmodule'), syntax_err_pos.group('garbage')) # Exists, but fails syntax check return good half and bad half
        else: return (1, None, None)

def on_modified(args):#
    global lint_timer
    
    # modificationType bitmask: 1 = insert text, 2 = delete text
    # We only care if the actual text changes, not if a bookmark was added
    if (args['modificationType'] & 1) or (args['modificationType'] & 2):
        if lint_timer:
            lint_timer.cancel() # Reset the clock
            
        # Start a 2.0 second countdown
        lint_timer = threading.Timer(0.5, run_linter)
        lint_timer.start()

# Clear out any old callbacks so we don't accidentally run 5 timers at once
editor.clearCallbacks(eval('SCINTILLANOTIFICATION.MODIFIED'))

# Tell Notepad++ to listen to our function every time a key is pressed
editor.callback(on_modified, [SCINTILLANOTIFICATION.MODIFIED])

# Run it once immediately right now just to test
run_linter()