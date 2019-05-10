import re
from typing import AnyStr, Match

from text_normalize import ru_cap, r_group, r_bracketed, r_quoted, r_capitalized_ru, r_alias_prefix, \
  r_alias_quote_regex_replacer

sf = '[а-я]{1,3}'

r_few_words = r'\s+[А-Я]{1}[а-я\-, ]{1,80}'
r_few_words_s = r'\s+[А-Яа-я\-, ]{0,80}'

ORG_TYPES_re = [
  ru_cap('Акционерное общество'), 'АО',
  ru_cap('Закрытое акционерное общество'), 'ЗАО',
  ru_cap('Открытое акционерное общество'), 'ОАО',
  ru_cap('Государственное автономное учреждение'),
  ru_cap('Муниципальное бюджетное учреждение'),
  ru_cap('Общественная организация'),
  ru_cap('Общество с ограниченной ответственностью'), 'ООО',
  ru_cap('Некоммерческая организация'),
  ru_cap('Благотворительный фонд'),
  ru_cap('Индивидуальный предприниматель'), 'ИП',

  r'[Фф]онд[а-я]{0,2}' + r_few_words_s,

]

r_types_ = '|'.join([x for x in ORG_TYPES_re])
r_types = r_group(f'{r_types_}', 'type')

r_name_a = r'([–А-Яa-я\- ]{0,30})'
_r_name = r'[А-ЯA-Z][А-Яa-яA-Za-z\- –\[\] ]{0,40}[a-я]'
r_name = r_group(_r_name, 'name')
r_name_alias = r_group(_r_name, 'alias')

r_quoted_name = r_group(r_quoted(r_name))
r_quoted_name_alias = r_group(r_quoted(r_name_alias))

r_alias = r_group(r".{0,140}" + r_alias_prefix + r'\s*' + r_quoted_name_alias)

r_type_and_name = r_types + r_name_a + r_quoted_name

r_alter = r_group(r_bracketed(r'.{1,70}') + r'{0,2}', 'alt_name')
complete_re_str = r_type_and_name + '\s*' + r_alter + r_alias + '?'
complete_re = re.compile(complete_re_str, re.MULTILINE)

alias_quote_regex = [
  r_alias_quote_regex_replacer,

  (re.compile(r_quoted_name + '\s*' + r'([(])(' + r_types_ + r')([)])'), r'\6 «\3» '),
  (re.compile(
    r_group(ru_cap('Индивидуальный предприниматель') + '|ИП\s+') + r_group(r_group(r_capitalized_ru + '\s*') + r'{3}')),
   r'\1«\2»'),
]


def find_org_names(txt):
  def clean(x):
    if x is None:
      return x
    return x.replace('\t', ' ').replace('\n', ' ').replace(' – ', '-')

  def to_dict(m: Match[AnyStr]):

    return {
      'type': (clean(m['type']), m.span('type')),
      'type_ext': (clean(m[2]), m.span(2)),
      'name': (clean(m['name']), m.span('name')),
      'alt_name': (clean(m['alt_name']), m.span('alt_name')),
      'alias': (clean(m['alias']), m.span('alias')),
    }

  org_names = {}

  i = 0
  for r in re.finditer(complete_re, txt):
    org = to_dict(r)
    _name = org['name'][0]
    if _name not in org_names:
      org_names[_name] = org
    i += 1

  return list(org_names.values())


if __name__ == '__main__':
  print(r_group(r_capitalized_ru, 'alias'))
  pass