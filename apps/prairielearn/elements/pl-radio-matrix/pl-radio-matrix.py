import random
from enum import Enum
from typing import Any
import copy
from collections import Counter


import chevron
import lxml.html
import prairielearn as pl


ALLOW_BLANK_DEFAULT = False
ARIA_LABEL_DEFAULT = "Radio element"
BLANK_ANSWER = " "
BUILTIN_GRADING_DEFAULT = True
FIXED_OPTIONS_ORDER_DEFAULT = False
FIXED_STATEMENTS_ORDER_DEFAULT = False
HIDE_SCORE_BADGE_DEFAULT = False
SHOW_HELP_TEXT_DEFAULT = False
RADIO_MATRIX_REPEAT_HEADER_DEFAULT = ""
RADIO_MATRIX_STATEMENT_COLUMN_WIDTH = "40%"
MIN_RESPONSE_PER_OPTION_DEFAULT = None
MAX_RESPONSE_PER_OPTION_DEFAULT = None
NA_DEFAULT = False
PARTIAL_CREDIT_DEFAULT = True
RESET_BUTTON_DEFAULT = False
WEIGHT_DEFAULT = 1

STATEMENT_TAG_VARIANT_STR_LIST = ["pl-statement", "pl_statement"]
OPTION_TAG_VARIANT_STR_LIST = ["pl-option", "pl_option"]


# Preset Options
PRESET_OPTIONS_DEFAULT = None
PRESET_OPTIONS_VARIANT_NAME_LIST = frozenset([
    "agreement-4", "agreement-5", "agreement-6", "agreement-7",
    "frequency-4", "frequency-5", "frequency-6", "frequency-7",
    "satisfaction-4", "satisfaction-5", "satisfaction-6", "satisfaction-7",
    "likelihood-4", "likelihood-5", "likelihood-6", "likelihood-7",
    "quality-4", "quality-5", "quality-6", "quality-7"
])

PRESET_OPTIONS_DEFAULT_MAP = {
    "agreement": [
        {"index": 0, "name": "Strongly Disagree", "html": "Strongly Disagree"},
        {"index": 1, "name": "Disagree", "html": "Disagree"},
        {"index": 2, "name": "Somewhat Disagree", "html": "Somewhat Disagree"},
        {"index": 3, "name": "Neutral", "html": "Neutral"},
        {"index": 4, "name": "Somewhat Agree", "html": "Somewhat Agree"},
        {"index": 5, "name": "Agree", "html": "Agree"},
        {"index": 6, "name": "Strongly Agree", "html": "Strongly Agree"} 
    ],
    "frequency": [
        {"index": 0, "name": "Never", "html": "Never"},
        {"index": 1, "name": "Rarely", "html": "Rarely"},
        {"index": 2, "name": "Infrequently", "html": "Infrequently"},
        {"index": 3, "name": "Sometimes", "html": "Sometimes"},
        {"index": 4, "name": "Frequently", "html": "Frequently"},
        {"index": 5, "name": "Often", "html": "Often"},
        {"index": 6, "name": "Always", "html": "Always"}
    ],
    "satisfaction": [
        {"index": 0, "name": "Strongly Dissatisfied", "html": "Strongly Dissatisfied"},
        {"index": 1, "name": "Dissatisfied", "html": "Dissatisfied"},
        {"index": 2, "name": "Somewhat Dissatisfied", "html": "Somewhat Dissatisfied"},
        {"index": 3, "name": "Neutral", "html": "Neutral"},
        {"index": 4, "name": "Somewhat Satisfied", "html": "Somewhat Satisfied"},
        {"index": 5, "name": "Satisfied", "html": "Satisfied"},
        {"index": 6, "name": "Strongly Satisfied", "html": "Strongly Satisfied"}
    ],
    "likelihood":[
        {"index": 0, "name": "Very Unlikely", "html": "Very Unlikely"},
        {"index": 1, "name": "Unlikely", "html": "Unlikely"},
        {"index": 2, "name": "Somewhat Unlikely", "html": "Somewhat Unlikely"},
        {"index": 3, "name": "Neutral", "html": "Neutral"},
        {"index": 4, "name": "Somewhat Likely", "html": "Somewhat Likely"},
        {"index": 5, "name": "Likely", "html": "Likely"},
        {"index": 6, "name": "Very Likely", "html": "Very Likely"}
    ],
    "quality":[
        {"index": 0, "name": "Poor", "html": "Very Poor"},
        {"index": 1, "name": "Inadequate", "html": "Inadequate"},
        {"index": 2, "name": "Below Average", "html": "Below Average"},
        {"index": 3, "name": "Average", "html": "Average"},
        {"index": 4, "name": "Above Average", "html": "Above Average"},
        {"index": 5, "name": "Great", "html": "Great"},
        {"index": 6, "name": "Excellent", "html": "Excellent"}
    ]}




RADIO_MATRIX_MUSTACHE_TEMPLATE_NAME = "pl-radio-matrix.mustache"


def get_form_name(
    answers_name: str, index: int) -> str:
    return f"{answers_name}-radio-{index}"



def legal_answer(answer: int, options: list[Any]) -> bool:
    """Check that the given answer is within the range of the given counter type."""
    return -1 <= answer < len(options)

def get_radio_matrix_select_options(
    options_list: list[Any], selected_value: int
) -> list[dict[str, Any]]:
    def transform(i: int, opt: Any) -> dict[str, Any]:
        index = i
        return {
            "index": index,
            "value": opt,
            "selected": "selected" if index == selected_value else None,
        }

    return [transform(i, opt) for i, opt in enumerate(options_list)]

def categorize_matches(
    element: lxml.html.HtmlElement,
) -> tuple[list[dict[str, int | str]], list[dict[str, int | str]]]:
    options = {}
    statements = []
    index = 0

    preset_option = pl.get_string_attrib(element, "preset-options", PRESET_OPTIONS_DEFAULT)
    preset_option = preset_option.strip() if preset_option is not None else None

    if not (preset_option is None) and not (preset_option in PRESET_OPTIONS_VARIANT_NAME_LIST):
        raise ValueError(
            f"\"{preset_option}\" is not a valid `preset-options` variant."
        )

    # Sort the elements so that pl-options come first.
    children = element[:]
    children.sort(key=lambda child: child.tag)

    def make_option(name: str, html: str) -> dict[str, int | str]:
        nonlocal index
        option = {"index": index, "name": name, "html": html}
        index += 1
        return option

    for child in children:
        if child.tag in OPTION_TAG_VARIANT_STR_LIST:

            if not (preset_option is None):
                raise ValueError(
                    'Note that `preset-options` attribute and `pl-options` tags are  mutually exclusive. Providing both of them will throw an error.'
                )

            pl.check_attribs(child, required_attribs=[], optional_attribs=["name"])
            child_html = pl.inner_html(child)
            option_name = pl.get_string_attrib(child, "name", child_html)


            option = make_option(option_name, child_html)
            options[option_name] = option

        elif child.tag in STATEMENT_TAG_VARIANT_STR_LIST:
            builtin_grading = pl.get_boolean_attrib(element, "builtin-grading", BUILTIN_GRADING_DEFAULT)
            if builtin_grading:
                pl.check_attribs(child, required_attribs=["match"], optional_attribs=[])
                child_html = pl.inner_html(child)
                match_name = pl.get_string_attrib(child, "match")
                if match_name not in options:
                    new_option = make_option(match_name, match_name)
                    options[match_name] = new_option

                # A statement object has: the name attribute of the correct matching option; and
                # the html content.
                statement = {"match": match_name, "html": child_html}
                statements.append(statement)
            else:
                pl.check_attribs(child, required_attribs=[], optional_attribs=[])
                child_html = pl.inner_html(child)
 
                statement = { "html": child_html}
                statements.append(statement)

    if preset_option is None:
        return list(options.values()), statements
    else:
        delimiter_idx = preset_option.find("-")
        preset_option_list = []
        if delimiter_idx != -1:
            preset_option_name = preset_option[ :delimiter_idx]
            preset_option_size = int(preset_option[delimiter_idx+1:])
            if preset_option_name in PRESET_OPTIONS_DEFAULT_MAP:
                preset_option_list = copy.deepcopy(PRESET_OPTIONS_DEFAULT_MAP[preset_option_name])
                if preset_option_size == 6:
                    preset_option_list = [
                        {"index": i, "name": item["name"], "html": item["html"] }
                        for i, item in enumerate(item for item in preset_option_list if item["index"]!=3)
                    ]
                elif preset_option_size == 5:
                    preset_option_list = [
                        {"index": i, "name": item["name"], "html": item["html"] }
                        for i, item in enumerate(item for item in preset_option_list if item["index"]!=2 and item["index"]!=4)
                    ]
                elif preset_option_size == 4:
                    preset_option_list = [
                        {"index": i, "name": item["name"], "html": item["html"] }
                        for i, item in enumerate(item for item in preset_option_list if item["index"]!=2 and item["index"]!=3 and item["index"]!=4)
                    ]
             
        preset_option_list.sort(key=lambda key: key["index"])
        return preset_option_list, statements

    

def prepare(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)

    required_attribs = ["answers-name"]
    optional_attribs = [
        "allow-blank",
        "aria-label",
        "blank",
        "builtin-grading",
        "reset-button",
        "counter-type",
        "display",
        "fixed-options-order",
        "fixed-order",
        "hide-score-badge",
        "min-response-per-option",
        "max-response-per-option",
        "not-applicable",
        "number-options",
        "number-statements",
        "options-placement",
        "partial-credit",
        "preset-options",
        "radio-matrix-statement-column-width",
        "repeat-header",
        "reset-button",
        "show-help-text",
        "weight",
    ]
    pl.check_attribs(element, required_attribs, optional_attribs)
    name = pl.get_string_attrib(element, "answers-name")
    pl.check_answers_names(data, name)

    builtin_grading = pl.get_boolean_attrib(element, "builtin-grading", BUILTIN_GRADING_DEFAULT)
    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)
    

    if not builtin_grading:
        if pl.has_attrib(element, "weight"):
            raise ValueError(
                '"weight" should not be set when builtin-grading is false.'
            )

        for child in element:
            if child.tag in STATEMENT_TAG_VARIANT_STR_LIST:
                if pl.has_attrib(child, "match"):
                    raise ValueError(
                        f'"match" on {child.tag} should not be set when builtin-grading is false.'
                    )
    else:
        preset_option = pl.get_string_attrib(element, "preset-options", PRESET_OPTIONS_DEFAULT)
        if preset_option is not None:
            raise ValueError("Cannot enable preset options when builtin grading is enabled")

    options, statements = categorize_matches(element)


    # Choose and randomize the options and statements. Each can be in a fixed order.
    fixed_statements_order = pl.get_boolean_attrib(
        element, "fixed-order", FIXED_STATEMENTS_ORDER_DEFAULT
    )
    fixed_options_order = pl.get_boolean_attrib(
        element, "fixed-options-order", FIXED_OPTIONS_ORDER_DEFAULT
    )

    number_statements = pl.get_integer_attrib(
        element, "number-statements", len(statements)
    )
    number_options = pl.get_integer_attrib(element, "number-options", len(options))
    nota = pl.get_boolean_attrib(element, "not-applicable", NA_DEFAULT)

    if fixed_statements_order:
        if number_statements < len(statements):
            # Take a random sampling, but maintain the original order of the statements.
            indices = random.sample(range(len(statements)), number_statements)
            statements = [statements[i] for i in sorted(indices)]
        # Otherwise, just use all the statements as-is.
    # Shuffle or sample the statements.
    elif number_statements < len(statements):
        statements = random.sample(statements, number_statements)
    else:
        random.shuffle(statements)

    # Organize the list of options to use.
    # First, select all the options associated with the chosen statements.
    needed_options = []
    distractors = []
    if builtin_grading:
        needed_options_keys = {s["match"] for s in statements}
        needed_options, distractors = pl.partition(
            options, lambda opt: opt["name"] in needed_options_keys
        )
    else:
        needed_options = options


    if len(needed_options) < number_options:
        # The limit is set above the # of options needed to match the chosen statements.
        # Add distractor options; and None of the Above if needed.
        more_needed = number_options - len(needed_options)
        if more_needed >= len(distractors):
            # Use all options, both correct and distractors.
            needed_options = options
            # Add NOTA if that's still not enough.
            if more_needed > len(distractors):
                nota = True
        else:
            # Add a sample of the distractors.
            distractor_sample = random.sample(distractors, more_needed)
            needed_options_keys = needed_options_keys.union({
                o["name"] for o in distractor_sample
            })
            needed_options = [o for o in options if o["name"] in needed_options_keys]
        options = needed_options
        if not fixed_options_order:
            random.shuffle(options)
        

    elif len(needed_options) > number_options:
        # The limit is set below the # of options needed.
        # Add None of the Above to compensate.

        if fixed_options_order:
            # Take a random sampling, but maintain the original order of the options.
            indices = random.sample(range(len(needed_options)), number_options)
            options = [needed_options[i] for i in sorted(indices)]
        else:
            options = random.sample(needed_options, number_options)
        nota = True
        
    else:
        # The number of needed options matches the total options.
        options = needed_options
        if not fixed_options_order:
            random.shuffle(options)
        

    if nota:
        options.append({
            "index": len(options),
            "name": "__nota__",
            "html": "Not Applicable",
        })

    

    # Build the options to display to the student.
    chosen_option_names = []
    display_options = []
    for opt in options:
        keyed_option = {"key": opt["name"], "html": opt["html"]}
        display_options.append(keyed_option)
        chosen_option_names.append(opt["name"])

     # Build the statements to display to the student.
    if builtin_grading:
        display_statements = []
        correct_matches = []
        for i, statement in enumerate(statements):
            if nota and statement["match"] not in chosen_option_names:
                match_index = len(options) - 1
            else:
                match_index = chosen_option_names.index(statement["match"])
            keyed_statement = {
                "key": str(i),
                "html": statement["html"],
                "match": statement["match"],
            }
            

            display_statements.append(keyed_statement)
            correct_matches.append(match_index)

        data["params"][name] = (display_statements, display_options)
        data["correct_answers"][name] = correct_matches
    else:
        display_statements = []
        for i, statement in enumerate(statements):
            keyed_statement = {
                "key": str(i),
                "html": statement["html"],
            }
            display_statements.append(keyed_statement)

        data["params"][name] = (display_statements, display_options)
        data["correct_answers"][name] = None

    min_response_per_option = pl.get_integer_attrib(
            element, "min-response-per-option", MIN_RESPONSE_PER_OPTION_DEFAULT
        )
    max_response_per_option = pl.get_integer_attrib(
            element, "max-response-per-option", MAX_RESPONSE_PER_OPTION_DEFAULT
        )

    radio_solvability_error = ""
    
    if min_response_per_option is not None and max_response_per_option is not None and min_response_per_option > max_response_per_option:
        radio_solvability_error += "The minimum number of columns specified must be equal or lower to the maximum number of columns. "
    

    if min_response_per_option is not None:
        if min_response_per_option < 0:
            radio_solvability_error += "The minimum number of columns specified should be 0 or above. "
        if min_response_per_option * len(options) > len(statements):
            radio_solvability_error += "The question is not solvable since the minimum option required is too high. "
        if builtin_grading:
            correct_counts = Counter(statement["match"] for statement in display_statements)
            min_answer_count = min(correct_counts.values())
            if min_answer_count < min_response_per_option:
                radio_solvability_error += "The question is not solvable since the minimum correct options are lower than the minimum options required. "

    if max_response_per_option is not None:
        if max_response_per_option < 1:
            radio_solvability_error += "The maximum number of columns specified should be 1 or above. "
        if max_response_per_option * len(options) < len(statements) and not allow_blank:
            radio_solvability_error += "The question is not solvable since the maximum options required is too low. "
        if builtin_grading:
            correct_counts = Counter(statement["match"] for statement in display_statements)
            max_answer_count = max(correct_counts.values())
            if max_answer_count > max_response_per_option:
                radio_solvability_error += "The question is not solvable since the maximum correct options are higher than the maximum options required. "


    
    if radio_solvability_error != "":
        raise ValueError(radio_solvability_error)




def parse(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, "answers-name")
    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)

    display_statements, display_options = data["params"][name]
    submitted_answers = data["submitted_answers"]

    for i in range(len(display_statements)):
        expected_html_name = get_form_name(name, i)
        try:
            submitted_answer_val = submitted_answers[expected_html_name]
            student_answer = None
            if submitted_answer_val is None:
                student_answer = -1
            else:
                student_answer = int(submitted_answer_val)
        except (ValueError, TypeError):
            # This could happen if the not parsable.
            data["format_errors"][expected_html_name] = (
                "The submitted answer is not a legal option."
            )
            continue
        except KeyError:
            # Unselected radio buttons are omitted from the submitted form data.
            if allow_blank:
                student_answer = -1
            else:
                data["format_errors"][expected_html_name] = "No answer was submitted."
                continue

        # A blank is a valid submission from the HTML, but causes a format error.
        if student_answer == -1 and not allow_blank:
            data["format_errors"][expected_html_name] = (
                "The submitted answer was left blank."
            )
        elif not legal_answer(student_answer, display_options ):
            data["format_errors"][expected_html_name] = (
                "The submitted answer is invalid."
            )


    min_response_per_option = pl.get_integer_attrib(
        element, "min-response-per-option", MIN_RESPONSE_PER_OPTION_DEFAULT
    )
    max_response_per_option = pl.get_integer_attrib(
        element, "max-response-per-option", MAX_RESPONSE_PER_OPTION_DEFAULT
    )
    if min_response_per_option is not None or max_response_per_option is not None :
        column_counts = [0] * len(display_options)
        for i in range(len(display_statements)):
            form_name = get_form_name(name, i)
            try:
                answer = int(submitted_answers[form_name])
            except (KeyError, ValueError, TypeError):
                continue
            if 0 <= answer < len(column_counts) and form_name not in data["format_errors"]:
                column_counts[answer] += 1
        
        for count in column_counts:
            if min_response_per_option is not None and count < min_response_per_option:
                for i in range(len(display_statements)):
                    form_name = get_form_name(name, i)
                    if min_response_per_option ==1:
                        data["format_errors"].setdefault(
                            form_name ,
                            f"At least {min_response_per_option} response must select each option.",
                        )
                    else:
                        data["format_errors"].setdefault(
                            form_name ,
                            f"At least {min_response_per_option} responses must select each option.",
                        )
            elif max_response_per_option is not None and count > max_response_per_option:
                for i in range(len(display_statements)):
                    form_name = get_form_name(name, i)
                    if max_response_per_option ==1:
                        data["format_errors"].setdefault(
                            form_name  ,
                            f"At most {max_response_per_option} response can be selected each option.",
                        )
                    else:
                        data["format_errors"].setdefault(
                            form_name  ,
                            f"At most {max_response_per_option} responses can be selected each option.",
                        )


                            


def parse_repeat_header_str_to_list(repeat_header_str: str) -> list[int]:
    repeat_header_col_count_str_list = repeat_header_str.split(',')
    ans_col_count_list = []
    for repeat_header_col_count_str in repeat_header_col_count_str_list:

        # Trim whitespace and ignore empty entry
        repeat_header_col_count_str_trimmed = repeat_header_col_count_str.strip()

        if (len(repeat_header_col_count_str_trimmed) == 0):
            continue

        try:
            repeat_header_col_count_str_trimmed_int =int(repeat_header_col_count_str_trimmed)
            if repeat_header_col_count_str_trimmed_int <0:
                raise ValueError(f'pl radio matrix display "repeat-header" column number must be a positive integer, got: {repeat_header_col_count_str} in {repeat_header_str}')
            ans_col_count_list.append(int(repeat_header_col_count_str_trimmed))
            
        except ValueError:
            raise ValueError(f'pl radio matrix display "repeat-header" column number must be an integer, got: {repeat_header_col_count_str} in {repeat_header_str}') from None

    return ans_col_count_list
            

def render(element_html: str, data: pl.QuestionData) -> str:
    element = lxml.html.fragment_fromstring(element_html)
    aria_label = pl.get_string_attrib(element, "aria-label", ARIA_LABEL_DEFAULT)
    show_help_text = pl.get_boolean_attrib(element, "show-help-text", SHOW_HELP_TEXT_DEFAULT)
    partial_credit = pl.get_boolean_attrib(
        element, "partial-credit", PARTIAL_CREDIT_DEFAULT
    )
    allow_blank = pl.get_boolean_attrib(element, "allow-blank", ALLOW_BLANK_DEFAULT)
    max_response_per_option = pl.get_integer_attrib(
        element, "max-response-per-option", MAX_RESPONSE_PER_OPTION_DEFAULT
    )


    name = pl.get_string_attrib(element, "answers-name")
    display_statements, display_options = data["params"].get(name, ([], []))
    
    builtin_grading = pl.get_boolean_attrib(element, "builtin-grading", BUILTIN_GRADING_DEFAULT)
    submitted_answers = data["submitted_answers"]
    repeat_header_col_count_list = parse_repeat_header_str_to_list(pl.get_string_attrib(element, "repeat-header", RADIO_MATRIX_REPEAT_HEADER_DEFAULT))

    if len(repeat_header_col_count_list) == 0:
        repeat_header_col_count_list.append(len(display_statements))

    statement_column_width_str = pl.get_string_attrib(element, "radio-matrix-statement-column-width", RADIO_MATRIX_STATEMENT_COLUMN_WIDTH)

    hide_score_badge = pl.get_boolean_attrib(
        element, "hide-score-badge", HIDE_SCORE_BADGE_DEFAULT
    )

    if not builtin_grading:
        hide_score_badge = True
        partial_credit = False

    show_answer_feedback = not hide_score_badge

    html = ""
    format_instructions = ""
    allow_blank_instruction = (
        "(You may leave this completely blank. If you choose not to, follow the next formatting instructions for your inputs.)"
        if allow_blank
        else ""
    )
    format_instructions += allow_blank_instruction
    with open(RADIO_MATRIX_MUSTACHE_TEMPLATE_NAME, "r", encoding="utf-8") as f:
        template = f.read()
    

    if data['panel'] == "question":
        partial_score = data["partial_scores"].get(name, {"score": None})
        score = partial_score.get("score", None)
        display_score_badge = score is not None and show_answer_feedback and builtin_grading

        radio_matrix_list = []

        curr_matrix_statement_list = []

        table_group_i = 0
        
        for statement_i, statement in enumerate(display_statements):
            form_name = get_form_name(name, statement["key"] )
            student_answer = int(submitted_answers.get(form_name, -1))
            if builtin_grading:
                correct_answer = data["correct_answers"][name][statement_i]
            else:
                correct_answer =None

            parse_error = data["format_errors"].get(form_name, None)

            statement_html = {
                "statement_name": form_name,
                "statement_id": pl.get_uuid(),
                "html": statement["html"].strip(),
                "statement_options": get_radio_matrix_select_options(
                    display_options, student_answer
                ),
                "is_even_row": len(curr_matrix_statement_list) % 2 == 0,
                "display_score_badge": display_score_badge,
                "correct": display_score_badge and correct_answer != None and student_answer == correct_answer,
                "parse_error": parse_error
            }

            if len(curr_matrix_statement_list) == repeat_header_col_count_list[table_group_i]:
                radio_matrix_list.append(
                    {
                        "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                        "statement_list": curr_matrix_statement_list
                    }
                )
                table_group_i = (table_group_i + 1) % len(repeat_header_col_count_list)
                curr_matrix_statement_list = []

            curr_matrix_statement_list.append(statement_html)

        radio_matrix_list.append(
            {   
                "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                "statement_list": curr_matrix_statement_list
            }
        )

        option_set = []
        for option in display_options:
            option_html = {
                "key": option["key"],
                "html": option["html"].strip(),
            }
            option_set.append(option_html)

        # Help Button Text Handling Section
        grading_text = ""
        if builtin_grading:
            if partial_credit: 
                grading_text = (
                    format_instructions
                    + "You will receive credit per radio selected, and feedback on which radios are filled out correctly."
                )
            else:
                grading_text = (
                    format_instructions
                    + "You will receive feedback on which radio are correct, but no partial credit unless the entire question is filled correctly."
                )
        else:
            grading_text = (
                    format_instructions
                    + "Grading will be performed manually. Please wait for the instructor's feedback."
                )
        info_params = {"format": True, "grading_text": grading_text}
        info = chevron.render(template, info_params).strip()
        max_options_warning_statement = ""
        if max_response_per_option is not None and max_response_per_option> 1:
            max_options_warning_statement = f"Please do not select more than the {max_response_per_option} options"
        elif max_response_per_option is not None and max_response_per_option == 1:
            max_options_warning_statement = f"Please do not select more than the {max_response_per_option} option"

        html_params: dict[str, str | bool | float | list[Any]] = {
            "aria_label": aria_label,
            "question": True,
            "name": name,
            "radio_matrix_list": radio_matrix_list,
            "radio-matrix-statement-column-width": statement_column_width_str,
            "options": option_set,
            "editable": data["editable"],
            "uuid": pl.get_uuid(),
            "builtin-grading": builtin_grading,
            "reset_button": pl.get_boolean_attrib(element, "reset-button", RESET_BUTTON_DEFAULT),
            "info": info,
            "show_help_text": show_help_text,
            "max_response_per_option": max_response_per_option,
            "has_max_response_per_option": max_response_per_option is not None,
            "max_options_warning_statement": max_options_warning_statement
        }

        if score is not None:
            score_type, score_value = pl.determine_score_params(score)
            html_params[score_type] = score_value

        with open(RADIO_MATRIX_MUSTACHE_TEMPLATE_NAME, encoding="utf-8") as f:
            html = chevron.render(f, html_params).strip()

    elif data["panel"] == "answer":
        correct_answer_list = data["correct_answers"].get(name, [])
        if not builtin_grading:
            return ""

        radio_matrix_list = []

        curr_matrix_statement_list = []

        table_group_i = 0
        
        for statement_i, statement in enumerate(display_statements):
            form_name = get_form_name(name, statement["key"] )

            # Set correct answer for the statement (builtin-grading should be True at this point)
            correct_answer = correct_answer_list[statement_i]

            statement_html = {
                "statement_name": form_name,
                "statement_id": pl.get_uuid(),
                "html": statement["html"].strip(),
                "statement_options": get_radio_matrix_select_options(
                    display_options, correct_answer
                ),
                "is_even_row": len(curr_matrix_statement_list) % 2 == 0,
            }

            if len(curr_matrix_statement_list) == repeat_header_col_count_list[table_group_i]:
                radio_matrix_list.append(
                    {
                        "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                        "statement_list": curr_matrix_statement_list
                    }
                )
                curr_matrix_statement_list = []

                table_group_i = (table_group_i + 1) % len(repeat_header_col_count_list)

            curr_matrix_statement_list.append(statement_html)

        radio_matrix_list.append(
            {   
                "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                "statement_list": curr_matrix_statement_list
            }
        )

        option_set = []
        for option in display_options:
            option_html = {"key": option["key"], "html": option["html"].strip()}
            option_set.append(option_html)

        html_params = {
            "answer": True,
            "aria_label": aria_label,
            "radio_matrix_list": radio_matrix_list,
            "radio-matrix-statement-column-width": statement_column_width_str,
            "options": option_set,
            "editable":False
        }

        with open(RADIO_MATRIX_MUSTACHE_TEMPLATE_NAME, encoding="utf-8") as f:
            html = chevron.render(f, html_params).strip()
    
    elif data["panel"] == "submission":
        parse_error = data["format_errors"].get(name, None)

        correct_answer_list = data["correct_answers"].get(name, [])

        if not (parse_error is None):
            return ""

        partial_score = data["partial_scores"].get(name, {"score": None})
        score = partial_score.get("score", None)
        radio_matrix_list = []

        curr_matrix_statement_list = []

        table_group_i = 0
        
        for statement_i, statement in enumerate(display_statements):
            form_name = get_form_name(name, statement["key"])
            student_answer = int(submitted_answers.get(form_name, -1))

            if builtin_grading:
                correct_answer = correct_answer_list[statement_i]
            else:
                correct_answer = None

            parse_error = data["format_errors"].get(form_name, None)

            display_score_badge = (
                parse_error is None and score is not None and show_answer_feedback and builtin_grading
            )

            statement_html = {
                "statement_name": form_name,
                "statement_id": pl.get_uuid(),
                "html": statement["html"].strip(),
                "statement_options": get_radio_matrix_select_options(
                    display_options, student_answer
                ),
                "is_even_row": len(curr_matrix_statement_list) % 2 == 0,
                "display_score_badge": display_score_badge,
                "correct": display_score_badge and correct_answer != None and student_answer == correct_answer,
                "parse_error": parse_error,
            }

            if len(curr_matrix_statement_list) == repeat_header_col_count_list[table_group_i]:
                radio_matrix_list.append(
                    {
                        "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                        "statement_list": curr_matrix_statement_list
                    }
                )
                curr_matrix_statement_list = []

                table_group_i = (table_group_i + 1) % len(repeat_header_col_count_list)

            curr_matrix_statement_list.append(statement_html)

        radio_matrix_list.append(
            {   
                "radio_matrix_name": f"{name}-radio-matrix-{len(radio_matrix_list)}",
                "statement_list": curr_matrix_statement_list
            }
        )

        option_set = []
        for option in display_options:
            option_html = {"key": option["key"], "html": option["html"].strip()}
            option_set.append(option_html)

        html_params = {
            "aria_label": aria_label,
            "submission": True,
            "radio_matrix_list": radio_matrix_list,
            "radio-matrix-statement-column-width": statement_column_width_str,
            "options": option_set,
            "display_score_badge": score is not None,
            "builtin-grading": builtin_grading
        }

        if html_params["display_score_badge"] and score is not None:
            score_type, score_value = pl.determine_score_params(score)
            html_params[score_type] = score_value

        with open(RADIO_MATRIX_MUSTACHE_TEMPLATE_NAME, encoding="utf-8") as f:
            html = chevron.render(f, html_params).strip()
    return html


    

def grade(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, "answers-name")
    if not pl.get_boolean_attrib(element, "builtin-grading", BUILTIN_GRADING_DEFAULT):
        return
    weight = pl.get_integer_attrib(element, "weight", WEIGHT_DEFAULT)
    partial_credit = pl.get_boolean_attrib(
        element, "partial-credit", PARTIAL_CREDIT_DEFAULT
    )
    display_statements, _ = data["params"][name]
    number_statements = len(display_statements)

    submitted_answers = data["submitted_answers"]
    correct_answers = data["correct_answers"].get(name, [])

    # Count the number of answers that are correct.
    num_correct = 0
    for i in range(number_statements):
        expected_html_name = get_form_name(name, i)
        student_answer = int(submitted_answers.get(expected_html_name, -1))
        correct_answer = correct_answers[i]
        if student_answer == correct_answer:
            num_correct += 1

    score = 0
    if not partial_credit and num_correct == number_statements:
        score = 1
    elif partial_credit:
        # EDC grading
        score = num_correct / number_statements
    data["partial_scores"][name] = {"score": score, "weight": weight}

