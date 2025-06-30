#!/bin/python3

import argparse
import json
import os
import re

from pathlib import Path

import bs4
import joblib
import requests
import markdownify
from vnmutils.paliutils import (
  pali_stem,
)
from vnmutils.mdutils import (
  SCUID_SEGMENT_PATHS,
  rewrite_suttacentral_links_in_folder,
)

ROOT_FOLDER = Path(os.path.dirname(__file__))
CACHE_FOLDER = ROOT_FOLDER.joinpath('.cache')
SCIDMAP_FILE = ROOT_FOLDER.joinpath('scidmap.json')

SC_API_URL = "https://suttacentral.net/api/publication/edition/pli-tv-vi-en-brahmali_scpub8-ed1-web_2022-02-10/files"

CONTENT_TAGS = {
  None,
  'p',
  'ul',
  'ol',
  'h3',
  'h4',
  'dl',
  'blockquote',
  'hr',
  'dd',
}

def sanitize_file_name(title: str) -> str:
  return re.sub(
    r'\s+', ' ',
    title.replace('\u00a0', ' ').replace('\u2013', '-').replace('\u2014', '-').replace(':', '').replace('.', '').replace(',', '').replace("/", " ").replace("\"", "“")
  ).strip()

def sanitize_appendix_html(soup) -> str:
  if not isinstance(soup, bs4.NavigableString):
    # TODO: Find SC Vinaya links and replace them with internal links
    # This will require running this script with the canon script
    note_links = soup.find_all('a', attrs={'role': "doc-noteref"})
    for note_link in note_links:
      note_link.decompose()
  return str(soup)

class BaseEssayConfig:
  def __init__(self, folder):
    self.subfolder = folder
  
  def set_output_folder(self, output_dir: Path):
    self.folder = output_dir.joinpath(self.subfolder)

  def set_url(self, relpath: str):
    self.url = relpath.replace(
      "./matter/",
      "https://suttacentral.net/edition/pli-tv-vi/en/brahmali/"
    ).replace(".html", "") + "?lang=en"

  def generate_files(self, vinaya_essay: str) -> None:
    pass

class SkipEssay(BaseEssayConfig):
  def __init__(self):
    super().__init__('')

class ImportEssay(BaseEssayConfig):
  def __init__(self, folder, split="h2"):
    super().__init__(folder)
    self.split_tag = split

  class FileWriteJob:
    def __init__(self, path: Path, html: str, url: str, previous):
      self.path = path
      self.url = url
      # HACK to fix https://github.com/suttacentral/bilara-data/pull/4279
      self.markdown = markdownify.markdownify(html).replace(
        'https://suttacentral.nethttps://suttacentral.net',
        'https://suttacentral.net'
      )
      self.previous = previous
      self.next = None
      if previous:
        previous.next = self
    
    def append(self, next):
      self.next = next
      next.previous = self
    
    def write_all(self):
      if self.previous:
        self.previous.write_all()
      self.write()

    def write(self):
      previous_link = ''
      next_link = ''
      if self.previous:
        previous_link = f"\n\nPrevious: [{self.previous.path.stem}](./{self.previous.path.name.replace(' ', '%20')})"
      if self.next:
        next_link = f"## Next section: [{self.next.path.stem}](./{self.next.path.name.replace(' ', '%20')})"
      return self.path.write_text(f"""## By Ajahn Brahmali

Source: <{self.url}>{previous_link}

{self.markdown}

{next_link}
  """)

  def generate_files(self, vinaya_essay: str) -> None:
    file_write_job = None
    soup = bs4.BeautifulSoup(vinaya_essay, 'html.parser')
    title = soup.find_all('h1')
    assert len(title) == 1, f"Found {len(title)} h1 tags"
    title = title[0].text
    url = self.url
    nav = soup.find_all('nav')
    if len(nav) == 1:
      cur_elem = nav[0]
    elif len(nav) == 0:
      cur_elem = soup.find_all('h1')[0].next_sibling
    else:
      raise Exception(f"Found {len(nav)} nav tags")
    fname = sanitize_file_name(title)
    cur_file = self.folder.joinpath(f"{fname}.md")
    html_content = ''
    while cur_elem.next_sibling:
      cur_elem = cur_elem.next_sibling
      if cur_elem.name == self.split_tag:
        file_write_job = ImportEssay.FileWriteJob(cur_file, html_content, url, file_write_job)
        html_content = ''
        title = cur_elem.text
        assert cur_elem.get('id'), f"Expected split tag {cur_elem} to have an id"
        url = self.url + f"#{cur_elem['id']}"
        if url in TITLE_OVERRIDES:
          title = TITLE_OVERRIDES[url]
        cur_file = self.folder.joinpath(f"{sanitize_file_name(title)}.md")
        continue
      if cur_elem.name in CONTENT_TAGS:
        html_content += sanitize_appendix_html(cur_elem)
        continue
      if cur_elem.name == 'section' and cur_elem['role'] == "doc-endnotes":
        # TODO: Actually include the endnotes and bibliography somehow
        break
      raise Exception(f"Unexpected tag \"{cur_elem.name}\" found in \"{self.folder.stem}\"")
    file_write_job.write_all()

PALI_ROOT_TO_GLOSSARY_ITEM = dict()

# Sometimes Ajahn Brahmali uses different word forms in the notes than in the
# appendix.  This mapping makes sure we add both forms.
OTHER_WORD_FORMS = {
  'vibbham': ['vibbhant'],
  'dūs': ['dūsent', 'dūsess', 'dūsessant'],
}

class ImportGlossary(BaseEssayConfig):
  def __init__(self, folder='Glosses', split="h3", linkto=False):
    super().__init__(folder)
    self.split_tag = split
    self.MIN_CONTENT_LENGTH = 100
    self.linkto = linkto
  
  def generate_files(self, vinaya_essay: str):
    soup = bs4.BeautifulSoup(vinaya_essay, 'html.parser')
    soup = soup.find('article')
    splits = soup.find_all(self.split_tag)
    for subhead in splits:
      pali_id = subhead.attrs['id']
      assert pali_id, f"Expected {subhead} to have an id"
      pali_term_elems = subhead.find_all('i', attrs={'lang': 'pli'})
      assert len(pali_term_elems) > 0, f"Expected \"\"\"{subhead}\"\"\" to have a <i lang='pli'> term"
      pali_term = []
      for pali_term_elem in pali_term_elems:
        pali_term.append(pali_term_elem.text)
        gloss_elem = pali_term_elem.next_sibling
      pali_term = " ".join(pali_term)
      gloss = str(gloss_elem)
      if "“" in pali_term:
        pali_term = pali_term.split(":")[0].strip()
        gloss = "“" + gloss
      if "“" in gloss:
        fname = sanitize_file_name(f"{pali_term} means {gloss}") + ".md"
      else:
        fname = sanitize_file_name(pali_term) + ".md"
      content = ""
      cur_elem = subhead.next_sibling
      while cur_elem and cur_elem.name != self.split_tag and cur_elem.name != 'section':
        assert cur_elem.name in CONTENT_TAGS, f"Unexpected tag \"{cur_elem.name}\" found in under \"{pali_term}\" in {self.url}"
        content += sanitize_appendix_html(cur_elem)
        cur_elem = cur_elem.next_sibling
      if len(content) < self.MIN_CONTENT_LENGTH:
        continue
      cur_file = self.folder.joinpath(fname)
      if self.linkto:  
        for w in re.split(r'\W+', pali_term):
          s = pali_stem(w)
          PALI_ROOT_TO_GLOSSARY_ITEM[s] = str(cur_file)
          if s in OTHER_WORD_FORMS:
            for a in OTHER_WORD_FORMS[s]:
              PALI_ROOT_TO_GLOSSARY_ITEM[a] = str(cur_file)
      content = markdownify.markdownify(content)
      if content.startswith(":   "):
        content = content[4:]
      cur_file.write_text(f"""## By Ajahn Brahmali

Source: <{self.url}#{pali_id}>

{content}
""")

ESSAY_CONFIGS = {
 './matter/foreword.html': SkipEssay(),
 './matter/preface.html': SkipEssay(),
 './matter/general-introduction.html': ImportEssay('General'),
 './matter/bu-vb-1-introduction.html': ImportEssay('The Bhikkhu Vibhanga'),
 './matter/bu-vb-2-introduction.html': ImportEssay('The Bhikkhu Vibhanga'),
 './matter/bi-vb-introduction.html': ImportEssay('The Bhikkhuni Vibhanga'),
 './matter/kd-1-introduction.html': ImportEssay('The Khandhakas'),
 './matter/kd-2-introduction.html': ImportEssay('The Khandhakas'),
 './matter/pvr-introduction.html': ImportEssay('The Parivara'),
 './matter/bibliography.html': SkipEssay(),
 './matter/abbreviations.html': SkipEssay(),
 './matter/appendix-glossary.html': SkipEssay(),
 './matter/appendix-terms.html': ImportGlossary(linkto=True),
 './matter/appendix-sectional.html': ImportGlossary(),
 './matter/appendix-furniture.html': ImportGlossary('Furniture', split="dt"),
 './matter/appendix-medical.html': ImportGlossary('Medical Terms', split="dt", linkto=False),
 './matter/appendix-plants.html': SkipEssay(),
 './matter/bi-vb-appendix-rules.html': ImportEssay('Specific Bhikkhuni Rules', split="h3"),
}
for relpath, config in ESSAY_CONFIGS.items():
  config.set_url(relpath)

TITLE_OVERRIDES = {
  "https://suttacentral.net/edition/pli-tv-vi/en/brahmali/general-introduction?lang=en#origin": "Origin of the Vinaya",
  "https://suttacentral.net/edition/pli-tv-vi/en/brahmali/general-introduction?lang=en#content": "Contents of the Vinaya",
  "https://suttacentral.net/edition/pli-tv-vi/en/brahmali/pvr-introduction?lang=en#pvr-1.12.16": "Pvr 1-2",
}

disk_memoizer = joblib.Memory(
  CACHE_FOLDER,
  verbose=0,
)
@disk_memoizer.cache()
def get_vinaya_essays() -> dict:
  r = requests.get(SC_API_URL)
  return r.json()

def main(output_dir:Path=Path('./Ajahn Brahmali')):
  SCUID_SEGMENT_PATHS.load_data_from_json(
    SCIDMAP_FILE.read_text(),
    output_dir.parent,
  )
  print("Generating Files from Ajahn Brahmali's Appendices...")
  vinaya_essays = get_vinaya_essays()
  for path, vinaya_essay in vinaya_essays.items():
    if path not in ESSAY_CONFIGS:
      raise Exception(f"No config for {path}")
    if isinstance(ESSAY_CONFIGS[path], SkipEssay):
      continue
    ESSAY_CONFIGS[path].set_output_folder(output_dir)
    if not ESSAY_CONFIGS[path].folder.exists():
      ESSAY_CONFIGS[path].folder.mkdir(parents=True)
    try:
      ESSAY_CONFIGS[path].generate_files(vinaya_essay)
    except Exception as e:
      print(f"ERROR Failed to generate {path}!")
      raise e
  print("  Done!")

  ROOT_FOLDER.joinpath('glossary.json').write_text(
    json.dumps(PALI_ROOT_TO_GLOSSARY_ITEM, indent=2)
  )
  print("  Wrote glossary.json to repo folder (regardless of output_dir)")

  rewrite_suttacentral_links_in_folder(output_dir)
  print("  Linked SuttaCentral URLs to local files")

if __name__ == '__main__':
  argparse = argparse.ArgumentParser(
    description="Generates Ajahn Brahmali's Vinaya Notes as .md Files."
  )
  argparse.add_argument(
    'output_dir',
    type=Path,
    default=Path('./Ajahn Brahmali'),
    nargs='?',
  )
  args = argparse.parse_args()
  main(output_dir=args.output_dir)