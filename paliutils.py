#!/bin/python3

import unicodedata

def normalize(text: str) -> str:
  """Nondestructively replaces equivelant characters with the standard form"""
  return unicodedata.normalize('NFC', text).replace('ṃ', 'ṁ')

PALI_ALPHABET = normalize(
  'a ā i ī u ū e o ṁ k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l ḷ v s h'
).split(' ')
PALI_CAPS = [l.upper() for l in PALI_ALPHABET]
PALI_ALPHABET_WITH_CAPS = PALI_ALPHABET + PALI_CAPS
PALI_SUFFIXES = [['amhase', 'esānaṁ'],
  ['attha', 'aṇīya', 'anīya', 'assaṁ', 'issaṁ', 'ittha', 'ittho', 'ismiṁ', 'usmiṁ', 'ānāti'],
  ['antī', 'asso', 'amha', 'anta', 'onta', 'unta', 'enta', 'assa', 'assā', 'issa', 'ismā', 'amhā', 'amhi', 'ānaṁ', 'asmā', 'asmiṁ', 'āyaṁ', 'āvin', 'āsaṁ', 'iṁsu', 'imha', 'imhā', 'imhi', 'iyaṁ', 'isaṁ', 'isuṁ', 'īnaṁ', 'umhā', 'umhi', 'uyaṁ', 'usaṁ', 'usmā', 'ussa', 'ūnaṁ', 'ūbhi', 'etha', 'etho', 'eraṁ', 'esaṁ'],
  ['ati', 'āti', 'ant', 'usā', 'esi', 'āsi', 'eti', 'ānā', 'āsā', 'āsa', 'aro', 'āni', 'ato', 'ani', 'anā', 'ana', 'esu', 'ehi', 'asā', 'aso', 'eso', 'āna', 'īni', 'ūni', 'āya', 'āyo', 'āsu', 'āhi', 'ito', 'iyo', 'ima', 'īsu', 'īhi', 'unā', 'uno', 'uyā', 'uyo', 'ūhi', 'ena', 'ema', 'emu'],
  ['aṁ', 'uṁ', 'iṁ', 'in'],
  ['i', 'ī', 'a', 'ā', 'o', 'u', 'ū', 'e']]
for i in range(len(PALI_SUFFIXES)):
  for j in range(len(PALI_SUFFIXES[i])):
    PALI_SUFFIXES[i][j] = normalize(PALI_SUFFIXES[i][j])
  PALI_SUFFIXES[i] = set(PALI_SUFFIXES[i])

# HACKS
COMPOUNDS = {
  'methunadhammo': ['methuna', 'dhammo'],
  'gāmūpacāro': ['gāma'], # because it glosses gāma alone in BuPj2!
  'paṭigaṇheyya': ['paṭiggaṇheyya'], # Pc34 spelling fix
}
MANUAL_NORMALIZATIONS = {
  # Bhikkhu Rules
  # Sg Rules
  ('So','bhikkhu','samanubhāsitabbo—'): ['samanubhāsitabbo'],
  ('So','bhikkhu','samanubhāsitabbo.'): ['samanubhāsitabbo'],
  ('Te', 'bhikkhū', 'samanubhāsitabbā.'): ['samanubhāsitabbā'],
  ('Cakkhussa','raho','nāma'): ['raho'],
  ('Sotassa','raho','nāma'): ['raho'],
  # Np Rules
  ("Imehi", "paccekacīvaracetāpannehīti"): ['paccekacīvaracetāpannehi'], # Np9
  ('no','ce','abhinipphādeti,','tattha','gantvā','tuṇhībhūtena','uddissa','ṭhātabbaṁ.'): ['tuṇhībhūtena','uddissa','ṭhātabbaṁ'], # Np10
  ('Accekaṁ','maññamānena','bhikkhunā','paṭiggahetabbaṁ','paṭiggahetvā','yāva','cīvarakālasamayaṁ','nikkhipitabbanti'): ['accekaṁ','maññamānena','bhikkhunā','paṭiggahetabbaṁ'], # Np28
  # Pc Rules
  ('Asantaṁ','nāma','bhikkhuṁ'): ['santa'],
  ('Punapavāraṇāpi','sāditabbāti'): ['punapavāraṇa'],
  ('Niccapavāraṇāpi','sāditabbāti'): ['niccapavāraṇa'],
  ('Aññatra','tathā','rūpappaccayāti'): ['aññatra','tathārūpappaccayā'],
  ('Adhikaraṇaṁ','nāma'): ['dhikaraṇa'],
  # Pd Rules
  ('Bhikkhū','paneva','kulesu','nimantitā','bhuñjantīti'): ['bhikkhu','paneva','kulesu'],
  ('Tehi','bhikkhūhi','sā','bhikkhunī','apasādetabbā—','“apasakka','tāva,','bhagini,','yāva','bhikkhū','bhuñjantī”ti.'): ['apasādetabbā','apasakka','tāva','bhagini','yāva','bhikkhū','bhuñjanti'],
  # Bhikkhuni Rules
  # Pj Rules
  ('Sā', 'bhikkhunī', 'samanubhāsitabbā.'): ['samanubhāsitabbā'],
  # Sg Rules
  ('Tā', 'bhikkhuniyo', 'samanubhāsitabbā.'): ['samanubhāsitabbā'],
  # Pc Rules
  ('Ehāyye', 'imaṁ', 'adhikaraṇaṁ', 'vūpasamehīti'): ['vūpasamehi'],
  ('Anāpucchā', 'ārāmaṁ', 'paviseyyāti'): ['ārāmaṁ', 'anāpucchā', 'paviseyya'], # word order is different in the rule
}

def stem(word: str) -> str:
  word = word.lower()
  for i, group in enumerate(PALI_SUFFIXES):
    n = len(PALI_SUFFIXES) - i
    suffix = word[-n:]
    if suffix in group:
      return word[:-n]
  return word

def unquote(quote: str) -> str:
  if quote.endswith('ti'):
    quote = quote[:-2]
    if quote[-1] == 'ā':
      quote = quote[:-1] + 'a'
    elif quote[-1] == 'ī':
      quote = quote[:-1] + 'i'
    elif quote[-1] == 'ū':
      quote = quote[:-1] + 'u'
    elif quote[-1] == 'n':
      quote = quote[:-1] + 'ṁ'
    return quote
  if quote.endswith(' nāma'):
    return quote[:-5]
  return quote

def sanitize(text: str, lower: bool=True) -> str:
  """Strips a string of all non-Pali characters
  returns what's left in lowercase if lower."""
  valids = PALI_ALPHABET_WITH_CAPS
  if lower:
    text = text.lower()
    valids = PALI_ALPHABET
  return ''.join(filter(
    valids.__contains__,
    normalize(text)
  ))

def pali_stem(word: str) -> str:
  return stem(sanitize(word))

def match_terms_to_root_text(terms: list[list[str]], root_text: list[list[str]]) -> list[tuple[int, int, int]]:
  """
  Args:
    terms: A list of the Vibangha's terms.
      For example: [['Yo', 'panāti'], ['bhikkhu', 'nāma']]
    root_text: A list of lines of the root text. Each list is split by word.
      For example: [['Yo', 'pana', 'bhikkhu'], [etc]]
  Returns:
    A list of tuples in the form: (line_number, start_index, end_index)
    One tuple for each term showing where in the root text that term can be found.
      For example (given the above input): [(0, 0, 1), (0, 2, 2)]
  Throws an Exception if:
    - a term cannot be found within a single line
    - terms are not found in the order they were passed in 
  """
  normalized_terms = []
  if len(terms) == 0:
    return normalized_terms
  for i, term in enumerate(terms):
    if tuple(term) in MANUAL_NORMALIZATIONS:
      normalized_terms.append(MANUAL_NORMALIZATIONS[tuple(term)])
      continue
    # Otherwise, do it automatically
    normalized_terms.append([sanitize(t) for t in term])
    # REMOVE THE QUOTE MARKS
    if "nāma" in normalized_terms[-1]:
      # Usually at the end, but some, like pli-tv-bu-vb-ss7:2.1,
      # contain the " nāma" in the middle! >.<
      nama = normalized_terms[i].index("nāma")
      normalized_terms[i] = normalized_terms[i][:nama]
    elif term[-1] == "hotīti": # final hoti's aren't necessary
      del normalized_terms[i][-1]
      if len(normalized_terms[i]) == 0: # unless they are
        normalized_terms[i] = ['hoti']
    else:
      normalized_terms[i][-1] = unquote(normalized_terms[i][-1])
    # SPLIT COMPOUNDS
    j = 0
    while j < len(normalized_terms[i]):
      if normalized_terms[i][j] in COMPOUNDS:
        compound = normalized_terms[i][j]
        normalized_terms[i] = normalized_terms[i][:j] + \
          COMPOUNDS[compound] + \
          normalized_terms[i][j+1:]
        j += len(COMPOUNDS[compound])
      else:
        j += 1

  for i, term in enumerate(normalized_terms):
    normalized_terms[i] = [stem(t) for t in term]
  
  normalized_root_text = []
  for line in root_text:
    normalized_root_text.append([stem(sanitize(t)) for t in line])
  
  output = []
  # Greedy Algorithm: just take the first match we find
  def _is_match(line_number, start_index, term):
    for i in range(start_index, start_index+len(term)):
      # Have to support partial matches.
      # This may break if a term is trimmed down too much by the stemmer
      # Will figure that out when it comes up...
      if term[i-start_index] not in normalized_root_text[line_number][i]:
        return False
    return True
  def _process_remaining_terms(line_number: int, index_within_line: int, term_index: int) -> bool:
    """
    Returns True if all terms have been matched.
    """
    nonlocal output
    while line_number < len(normalized_root_text):
      if index_within_line > len(normalized_root_text[line_number]) - len(normalized_terms[term_index]):
        line_number += 1
        index_within_line = 0
        continue
      if _is_match(line_number, index_within_line, normalized_terms[term_index]):
        loc = (line_number, index_within_line, index_within_line + len(normalized_terms[term_index]) - 1)
        if term_index > 0:
          if loc == output[-1] and len(normalized_terms[term_index]) != len(normalized_terms[term_index-1]):
            raise Exception(f"Terms of different lengths found at the same spot")
          if output[-1][0] == loc[0] and output[-1][1] + len(normalized_terms[term_index-1]) - 1 > loc[1]:
            raise Exception(f"I believe term {term_index} is partially overlapping the previous term. Already have {output}")
        output.append(loc)
        term_index += 1
        if term_index == len(normalized_terms):
          return True
        # Don't increment index_within_line as some terms overlap
        # unless the next is identical
        skip_index = index_within_line+len(normalized_terms[term_index-1])
        try:
          if normalized_root_text[line_number][skip_index] == normalized_root_text[line_number][skip_index-1]:
            index_within_line = skip_index
          if normalized_root_text[line_number][skip_index] == 'v' and normalized_root_text[line_number][skip_index+1] == normalized_root_text[line_number][skip_index-1]:
            index_within_line = skip_index+1
        except IndexError:
          pass
        continue
      index_within_line += 1
    return False
  line_number = 0
  index_within_line = 0
  term_index = 0
  while True:
    finished = _process_remaining_terms(line_number, index_within_line, term_index)
    if finished:
      return output
    term_index = len(output)
    if len(normalized_terms[term_index]) == 1 and normalized_terms[term_index][0].startswith('a'):
      normalized_terms[term_index][0] = normalized_terms[term_index][0][1:]
      line_number = output[-1][0]
      index_within_line = output[-1][1]
      continue
    break
  raise Exception(f"""Could not find \"{' '.join(normalized_terms[term_index])}\" in root text.
  Found: {output} so far...
  
  {normalized_root_text}

  """)    
