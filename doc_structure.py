import re
from typing import List

from text_tools import tokenize_text, np, untokenize


def _strip_left(tokens):
  for i in range(len(tokens)):
    if tokens[i] != '.' and tokens[i] != ' ' and tokens[i] != '\t':
      return i
  return len(tokens)


def roman_to_arabic(n):
  roman = n.upper()
  if not check_valid_roman(roman):
    return None

  keys = ['IV', 'IX', 'XL', 'XC', 'CD', 'CM', 'I', 'V', 'X', 'L', 'C', 'D', 'M']
  to_arabic = {'IV': '4', 'IX': '9', 'XL': '40', 'XC': '90', 'CD': '400', 'CM': '900',
               'I': '1', 'V': '5', 'X': '10', 'L': '50', 'C': '100', 'D': '500', 'M': '1000'}
  for key in keys:
    if key in roman:
      roman = roman.replace(key, ' {}'.format(to_arabic.get(key)))
  return sum(int(num) for num in roman.split())


def check_valid_roman(roman):
  invalid = ['IIII', 'VV', 'XXXX', 'LL', 'CCCC', 'DD', 'MMMM', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
  if any(sub in roman for sub in invalid):
    return False
  return True


def roman_might_be(wrd):
  try:
    return roman_to_arabic(wrd)
  except:
    return None


def string_to_ip(str):
  ret = []
  n = str.split('.')
  for c in n:
    try:
      ret.append(int(c))
    except:
      pass
  return ret


def get_tokenized_line_number(tokens: List, last_level):
  """
  :param tokens: list of stings, supposed to be lowercase
  :return: number, number_region, line???, level (for 1.1.1 it is 3)
  """

  if len(tokens) == 0:
    return None, (0, 0), last_level

  r = roman_might_be(tokens[0])
  if r is not None:
    # Roman number
    return [r], (0, 1), 0

  else:
    # Arabic (might be)
    # Searching for numbered lines
    token_index = 0

    if tokens[0] == 'статья' and len(tokens) >= 2:
      token_index = 1

    x = re.search(r'^(\d{1,2}($|\.)){1,6}', tokens[token_index], flags=re.MULTILINE)
    if x is not None:
      # found number
      n = string_to_ip(x.group(0))
      level = len(n)
      offset = token_index + 1  # tokens before actual text

      if len(tokens) > 2:
        if tokens[token_index + 1] == ')':
          level += 1
          offset += 1

        offset += _strip_left(tokens[offset:])

      return n, (0, offset), level


    else:
      # Number not found

      # searching for bulletpoints -
      # x = re.search(r'^\s*[\-|•]\s*', tokens[token_index], flags=re.MULTILINE)
      x = re.search(r'^[\-|•]', tokens[token_index], flags=re.MULTILINE)
      if x is not None:
        return [-1], (0, 1), last_level
      else:
        pass

  return None, (0, 0), last_level


class StructureLine():

  def __init__(self, level=0, number=[], bullet=False, span=(0, 0), text_offset=1, line_number=-1) -> None:
    super().__init__()
    self.number = number
    self.level = level
    self.bullet = bullet
    self.span = span
    self.text_offset = text_offset
    self._possible_levels = []
    self.line_number = line_number
    self.sequence_end = 0

  def __str__(self) -> str:
    return ('#{}  N:{}  L:{} -> PL:{}, '.format(self.minor_number, self.number, self.level, self._possible_levels))

  def get_median_possible_level(self):
    if len(self._possible_levels) == 0:
      return self.level

    counts = np.bincount(self._possible_levels)
    return np.argmax(counts)

  def get_parent_number(self):
    if len(self.number) > 1:
      return self.number[-2]

    return None

  def add_possible_level(self, l):
    self._possible_levels.append(l)

  def print(self, tokens_cc, suffix='', line_number=None):

    offset = '  .  ' * self.level

    number_str = '.'.join([str(x) for x in self.number])
    if self.bullet:
      number_str = '• '
    if self.numbered:
      number_str += '.'
    #         print(offset, number_str, (self.tokens_cc[span[0] + number_tokens:span[1]]))
    values = "not text so far"
    if tokens_cc is not None:
      values = self.to_string_no_number(tokens_cc)

    ln = self.line_number
    if line_number is not None:
      ln = line_number

    se = '+' * self.sequence_end
    #     if self.sequence_end>0:
    #       se=str(self.sequence_end)
    print('ds>{}\t {}\t'.format(ln, se), offset, number_str, values, suffix)

  def to_string_no_number(self, tokens_cc):
    return untokenize(tokens_cc[self.span[0] + self.text_offset: self.span[1]])

  def to_string(self, tokens):
    return untokenize(self.subtokens(tokens))

  def subtokens(self, tokens):
    return tokens[self.span[0]: self.span[1]]

  def get_numbered(self) -> bool:
    return len(self.number) > 0

  def get_minor_number(self) -> int:
    if (self.numbered):
      return self.number[-1]

  numbered = property(get_numbered)
  minor_number = property(get_minor_number)
  parent_number = property(get_parent_number)


class DocumentStructure:

  def __init__(self):
    self.structure: List[StructureLine] = None
    # self._detect_document_structure(text)

  def tokenize(self, _txt):
    return tokenize_text(_txt)

  def detect_document_structure(self, text):
    lines: List[str] = text.split('\n')

    line_number = 0

    last_level_known = 0

    structure = []

    tokens = []
    tokens_cc = []

    index = 0
    for __row in lines:
      line_number += 1

      line_tokens_cc = self.tokenize(__row.strip()) + ['\n']

      line_tokens = [s.lower() for s in line_tokens_cc]
      tokens_cc += line_tokens_cc
      tokens += line_tokens

      bullet = False

      if len(line_tokens) > 1:
        # not empty
        number, span, _level = get_tokenized_line_number(line_tokens, last_level_known)

        if number is None:
          number = []

        else:
          last_level_known = _level
          if number[-1] < 0:
            bullet = True
            number = []

        # level , section number, is it a bullet, span : (start, end)
        section_meta = StructureLine(
          level=_level,  # 0
          number=number,  # 1
          bullet=bullet,  # 3
          span=(index, index + len(line_tokens)),
          text_offset=span[1],
          line_number=len(structure)
        )

        # HEADLINE?
        if __row[:15].upper() == __row[:15]:
          section_meta.add_possible_level(0)

        structure.append(section_meta)

        index = len(tokens)

    # self.tokens_cc = tokens_cc  ## xxx: for debug only: TODO: remove this line

    structure = self.fix_structure(structure)

    self.structure = structure
    return tokens, tokens_cc

  def fix_structure(self, structure, verbose=False):

    numbered = self._get_numbered_lines(structure)
    if len(numbered) == 0:
      return structure

    for a in range(1):
      self._uplevel_non_numbered(structure)
      self._normalize_levels(structure)

      # self._fix_top_level_lines(numbered)
      self._update_levels(structure, verbose)

      self._uplevel_non_numbered(structure)
      self._normalize_levels(structure)

    return structure

  def find_min_level(self, structure):
    min_level = structure[0].level
    for s in structure:
      if s.level < min_level:
        min_level = s.level
    return min_level

  def _normalize_levels(self, structure):
    minlevel = self.find_min_level(structure)

    for s in structure:
      s.level -= minlevel

  def _get_numbered_lines(self, structure):
    numbered = []
    for s in structure:
      if s.numbered:
        # numbered
        numbered.append(s)
    return numbered

  def _update_levels(self, seq, verbose):
    # DEBUG
    for i in range(len(seq)):
      line = seq[i]

      # fixing:
      if len(line.number) < 2:
        line.level = line.get_median_possible_level()

      if verbose:
        line.print(self.tokens_cc, str(line.level) + '--->' + str(line._possible_levels) + ' i:' + str(i))

  def _uplevel_non_numbered(self, structure: List[StructureLine]):
    for s in structure:
      _last_level = 1
      if s.numbered:
        _last_level = s.level
      else:
        # non numbered
        if len(s._possible_levels) > 0:
          s.level = s.get_median_possible_level()
        elif s.level < _last_level + 1:
          s.level = _last_level + 1

  def _sequence_continues_fuzzy(self, structure: List, index: int, index_prev: int) -> float:

    if index_prev < 0:
      return 1.0
    if index >= len(structure):
      return 0.0
    if index_prev >= len(structure):
      return 0.0

    curr = structure[index]
    prev = structure[index_prev]

    yes = 0.0

    if curr.parent_number == prev.parent_number:
      yes += 4
    if curr.minor_number == prev.minor_number + 1:
      yes += 2
    if prev.level == curr.level:
      yes += 3

    if curr.parent_number is None and prev.parent_number is not None:
      yes += 1
    if curr.parent_number is not None and prev.parent_number is None:
      yes += 1

    if curr.minor_number == prev.minor_number + 2:  # hole
      yes += 1

    return yes / 9.0

  def _sequence_continues(self, structure: List, index: int, index_prev: int, level_delta=0, check_parent=True,
                          max_hole=0):
    def same_parent(a: StructureLine, b: StructureLine):
      if not check_parent:
        return True

      if len(a.number) > 1:
        if len(b.number) == 1:
          return True  # parent unknown
        elif len(b.number) > 1:
          return b.number[-2] == a.number[-2]

      if len(b.number) > 1:
        if len(a.number) == 1:
          return True  # parent unknown
        elif len(a.number) > 1:
          return b.number[-2] == a.number[-2]

      return True

    # ----

    if index_prev < 0:
      return True

    curr = structure[index]
    prev = structure[index_prev]

    if 0 <= (curr.minor_number - (prev.minor_number + 1)) <= max_hole and same_parent(curr, prev):
      return abs(curr.level - prev.level) <= level_delta

    return False

  def print_structured(self, doc, numbered_only=False):
    ln = 0
    for s in self.structure:
      if s.numbered or not numbered_only:
        s.print(doc.tokens_cc, str(s.level) + '->' + str(s._possible_levels), line_number=ln)
        ln += 1


# ---------------
def headline_probability(sentence, sentence_cc, prev_sentence, prev_value) -> float:
  """
  _cc == original case
  """

  NEG = -1
  value = 0

  if sentence == ['\n']:
    return NEG

  if len(sentence) < 2:
    return NEG

  if len(sentence) > 30:
    return NEG

  # headline may not go after another headline
  if prev_value > 0:
    value -= prev_value

  number, span, _level = get_tokenized_line_number(sentence, None)
  row = untokenize(sentence_cc[span[1]:])[:40]
  row = row.lstrip()

  if number is not None:

    # headline starts from 'статья'
    if sentence[0] == 'статья':
      value += 3

    if len(number) > 0:
      # headline is numbered

      minor_num = number[-1]

      if minor_num > 0:
        value += 1

      # headline number is NOT too big
      if minor_num > 40:
        value -= 1

      # headline is NOT a bullet
      if minor_num < 0:
        return NEG
    # ----
    if _level is not None:
      if _level == 0:
        value += 1

      if _level > 1:
        # headline is NOT a 1.2 - like-numbered
        return -_level

  # ------- any number
  # headline DOES not starts from lowercase
  if len(row) > 1:
    if row.lower()[0] == row[0]:
      value -= 1

  # headline is short enough
  if len(sentence) < 15:
    value += 1

  # headline is UPPERCASE
  if row.upper() == row:
    value += 2

  if prev_sentence == ['\n'] and sentence != ['\n']:
    value += 1

  return value
