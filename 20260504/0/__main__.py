import gettext
import locale
from . import PATH

def main():
	traslation = gettext.translation("wordcount", PATH, fallback=True)
	ngettext = translation.ngettext


locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
translation = gettext.translation("wordcount", PATH, fallback=TRUE)
ngettext = translation.ngettext

words = input().split()
n = len(words)
print(ngettext("Entered {} word", "Entered {} words", n).format(n))

