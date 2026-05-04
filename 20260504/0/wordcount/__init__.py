import gettext
import  locale

locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
translation = gettext.translation("wordcount", "po", fallback = True)
_, ngettext  = translation.gettext, translation.ngettext

translation_swan = gettext.translation("SWAN", "po", fallback = True)
_, ngettext_swan  = translation_swan.gettext, translation_swan.ngettext

word = input().split()
n = len(word)

print(ngettext("Entered {} word", "Entered {} word(s)", n).format(n))

print(ngettext_swan("Entered {} word", "Entered {} word(s)", n).format(n))
                                                                                                                                                                                     
