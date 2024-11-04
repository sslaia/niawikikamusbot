#!/usr/bin/env python3
"""
A bot for implementing the revision 2 of the page layout of Nias Wiktionary

On 7 Oct 2024 the Nias Wiki community decided to implement a new clean but more comprehensive layout called Revisi2. The definition has now its own section as well as the examples. New sections have also been added: synonyms, antonyms, etymology, etc. See https://nia.wiktionary.org/wiki/Wiktionary:Monganga_afo#Angetula_rafe_komunitas_(7_Okt_24):_Ta'oguna'%C3%B6_revisi_layout_sibohou


Use global -simulate option for test purposes. No changes to live wiki
will be done.

The following parameters are supported:

-always           The bot won't ask for confirmation when putting a page

-page             The page to work on

-file             The list of pages to work on

-summary:         Set the action summary message for the edit.

In addition the following generators and filters are supported but
cannot be set by settings file:

&params;
"""
#
# Sirus Laia, 2024
#
# Distributed under the terms of the MIT license.
#
import re
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)

# Function to find the language code section
def find_language_code(text):
    # List of valid language codes
    valid_language_codes = ['ar', 'de', 'en', 'es', 'fr', 'hu', 'id', 'it', 'jp', 'la', 'ms', 'nia', 'pt', 'sa', 'zh']

    # Regular expression to find the language code inside {{ }}
    match = re.search(r'\{\{([a-z]{2,3})\}\}', text)
    
    # If a match is found, check if it's in the valid language codes
    if match:
        language_code = match.group(1)
        if language_code in valid_language_codes:
            return language_code
    return None

# Function to find the part of speech section
def find_famoligo_section(text):
    # Define the possible part of speech sections
    part_of_speech = ['adjektiva', 'adverbia', 'interjeksi', 'konjungsi', 'nomina', 'partikel', 'preposisi', 'pronomina', 'verba']
    
    # Construct the regex pattern to search for any part of speech section
#    pattern = r'{{(' + '|'.join(part_of_speech) + r')}}\n(.*?)(?=\n{{|$)'
    pattern = r'{{(' + '|'.join(part_of_speech) + r')}}'
    match_part_of_speech = re.search(pattern, text)
    match_famoligo = re.search(r'{{famoligö}}', text)
    match_ipa = re.search(r'({{IPA.*}})', text)
    if match_ipa:
        famoligo_heading = "{{famoligö}}"  # Always set to "famoligö"
        famoligo_content = ":" + match_ipa.group().strip()
        return famoligo_heading, famoligo_content
    else:
        famoligo_heading = "{{famoligö}}"  # Always set to "famoligö"
        famoligo_content = ":{{IPA|ipa=|audio=}}"
        return famoligo_heading, famoligo_content
    return None, None

# Function to find definition and examples
def find_definisi_duma_section(text):
   
    # Regex to find the {{definisi}} heading and its content
    match_definisi = re.search(r'{{definisi}}\n(.*?)(?=\n{{|$)', text, re.DOTALL)
    match_duma = re.search(r'{{duma-duma}}\n(.*?)(?=\n{{|\[\[Berkas|\[\[File|\[\[Kategori|$)', text, re.DOTALL)
    
    if match_definisi and match_duma:
        definisi_duma = match_definisi.group().strip() + "\n\n" + match_duma.group().strip()
        return definisi_duma
    else:
        # Splitting the entry into lines
        lines = text.split("\n")
    
        definitions = []
        examples = []
        current_definition_number = 0
    
        for line in lines:
            if line.startswith("#* "):  # Identifying example sentences
                # Replacing #* with the current number and using double apostrophes for italicizing
                numbered_example = f":{current_definition_number}. {line[3:]}"
                examples.append(numbered_example)
            # this condition added in case # sign is attached directly to definition (chinese entries)
            elif line.startswith("#*"):  # Identifying example sentences
                # Replacing #* with the current number and using double apostrophes for italicizing
                numbered_example = f":{current_definition_number}. {line[2:]}"
                examples.append(numbered_example)
            elif line.startswith("# "):  # Identifying definitions
                current_definition_number += 1
                numbered_definition = f":{current_definition_number}. {line[2:]}"  # Replacing # with the current number
                definitions.append(numbered_definition)
            # this condition added in case # sign is attached directly to definition (chinese entries)
            elif line.startswith("#"):  # Identifying definitions
                current_definition_number += 1
                numbered_definition = f":{current_definition_number}. {line[1:]}"  # Replacing # with the current number
                definitions.append(numbered_definition)
    
        # Generating the output with subtitles
        definisi_duma = "{{definisi}}\n" + "\n".join(definitions) + "\n\n{{duma-duma}}\n" + "\n".join(examples)
        return definisi_duma

# Function to find the gambara heading and content
def find_gambara_section(text):
    # Find first the gallery if not skip
    match_gallery = re.search(r'<gallery>\n(.*)</gallery>', text, re.DOTALL)
    if match_gallery:
        gambara_heading = "{{gambara}}"
        image_list = match_gallery.group(1).strip()
        match_image = re.search(r'(.*)', image_list)
        match_image_split = match_image.group().split("|")
        gambara_content = "[[" + "|jmpl|".join(match_image_split) + "]]"
        return gambara_heading, gambara_content
    else:
        match_gambara_heading = re.search(r'{{gambara}}', text, re.DOTALL)
        match_berkas_content = re.search(r'(\[\[Berkas(.*?)\n)', text, re.DOTALL)
        match_file_content = re.search(r'(\[\[File(.*?)\n)', text, re.DOTALL)
        if match_berkas_content:
            gambara_heading = "{{gambara}}"
            gambara_content = match_berkas_content.group().strip()
            return gambara_heading, gambara_content
        elif match_file_content:
            gambara_heading = "{{gambara}}"
            gambara_content = match_file_content.group().strip()
            return gambara_heading, gambara_content
    return None, None

# Function to find the {{eluaha}} heading and content
def find_eluaha_section(text):
    match = re.search(r'{{eluaha}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        eluaha_heading = "{{eluaha}}"
        eluaha_content = match.group(1).strip()
        return eluaha_heading, eluaha_content
    return None, None

# Function to find the {{sinonim}} heading and content
def find_sinonim_section(text):
    match = re.search(r'{{sinonim}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        sinonim_heading = "{{sinonim}}"
        sinonim_content = match.group(1).strip()
        sinonim_content = sinonim_content.replace("*", ":")
        return sinonim_heading, sinonim_content
    return None, None

# Function to find the {{antonim}} heading and content
def find_antonim_section(text):
    match = re.search(r'{{antonim}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        antonim_heading = "{{antonim}}"
        antonim_content = match.group(1).strip()
        antonim_content = antonim_content.replace("*", ":")
        return antonim_heading, antonim_content
    return None, None

# Function to find the {{etimologi}} heading and content
def find_etimologi_section(text):
    match = re.search(r'{{etimologi}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        etimologi_heading = "{{etimologi}}"
        etimologi_content = match.group(1).strip()
        etimologi_content = etimologi_content.replace("*", ":")
        return etimologi_heading, etimologi_content
    return None, None

# Function to find the {{nitöngöni}} heading and content
def find_nitongoni_section(text):
    match = re.search(r'{{nitöngöni}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        nitongoni_heading = "{{nitöngöni}}"
        nitongoni_content = match.group(1).strip()
        nitongoni_content = nitongoni_content.replace("*", ":")
        return nitongoni_heading, nitongoni_content
    return None, None

# Function to find the {{fakhili}} heading and content
def find_fakhili_section(text):
    match = re.search(r'{{fakhili}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        fakhili_heading = "{{fakhili}}"
        fakhili_content = match.group(1).strip()
        fakhili_content = fakhili_content.replace("*", ":")
        return fakhili_heading, fakhili_content
    return None, None

# Function to find the {{daha}} heading and content
def find_daha_section(text):
    match = re.search(r'{{daha}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        daha_heading = "{{daha}}"
        daha_content = match.group(1).strip()
        daha_content = daha_content.replace("*", ":")
        return daha_heading, daha_content
    return None, None

# Function to find the {{fakhai}} heading and content
def find_fakhai_section(text):
    match = re.search(r'{{fakhai}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        fakhai_heading = "{{fakhai}}"
        fakhai_content = match.group(1).strip()
        fakhai_content = fakhai_content.replace("*", ":")
        return fakhai_heading, fakhai_content
    return None, None

# Function to find the {{baero}} heading and content
def find_baero_section(text):
    match = re.search(r'{{baero}}\n(.*?)(?=\n{{|\[\[Kategori|$)', text, re.DOTALL)
    if match:
        baero_heading = "{{baero}}"
        baero_content = match.group(1).strip()
        baero_content = baero_content.replace(":", "*")
        return baero_heading, baero_content
    return None, None

# Function to find the {{umbu}} heading and content
def find_umbu_section(text):
    match = re.search(r'{{umbu}}\n(.*?)(?=\n\[\[Kategori|$)', text, re.DOTALL)
    if match:
        umbu_heading = "{{umbu}}"
        umbu_content = match.group(1).strip()
        return umbu_heading, umbu_content
    return None, None

# Function to find the categories
def find_kategori(text):
    existing_kategori = "\n".join([line for line in text.splitlines() if line.startswith("[[Kategori")]).strip()
    match_kategori = re.search(r'No mufareso', existing_kategori)
    if match_kategori:
        kategori = existing_kategori.replace("No mufareso", "Awena mufareso")
        return kategori
    else:
        kategori = f"{existing_kategori}\n[[Kategori:Awena mufareso]]"
        return kategori
#    return existing_kategori

class NiaWikikamusBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    ConfigParserBot,  # A bot which reads options from scripts.ini setting file
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    """
    A simple bot for implementing the revision 2 of the page layout of Nias Wiktionary.

    :ivar summary_key: Edit summary message key. The message that should be
        used is placed on /i18n subdirectory. The file containing these
        messages should have the same name as the caller script (i.e. basic.py
        in this case). Use summary_key to set a default edit summary message.

    :type summary_key: str
    """

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'summary': 'Add the missing sections from Revisi2 (see community decision 7 Oct 24).'
    }

    #
    # the main function for page manipulation
    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text

        # Find the language code
        language_code = find_language_code(text)

        # Find the famoligo section
        famoligo_heading, famoligo_content = find_famoligo_section(text)

        # Find the definisi section
        definisi_duma = find_definisi_duma_section(text)

        # Find the gambara section
        gambara_heading, gambara_content = find_gambara_section(text)

        # Find the eluaha section
        eluaha_heading, eluaha_content = find_eluaha_section(text)

        # Find the sinonim section
        sinonim_heading, sinonim_content = find_sinonim_section(text)

        # Find the antonim section
        antonim_heading, antonim_content = find_antonim_section(text)

        # Find the etimologi section
        etimologi_heading, etimologi_content = find_etimologi_section(text)

        # Find the nitongoni section
        nitongoni_heading, nitongoni_content = find_nitongoni_section(text)

        # Find the fakhili section
        fakhili_heading, fakhili_content = find_fakhili_section(text)

        # Find the daha section
        daha_heading, daha_content = find_daha_section(text)

        # Find the fakhai section
        fakhai_heading, fakhai_content = find_fakhai_section(text)
        
        # Find the baero section
        baero_heading, baero_content = find_baero_section(text)

        # Find the umbu section
        umbu_heading, umbu_content = find_umbu_section(text)
        
        # Find the categories
        kategori = find_kategori(text)
       
        #
        #
        # Build the updated text in the desired order
        updated_text = ""
       
        if language_code:
           updated_text += f"{{{{{language_code}}}}}\n\n"
           
        if famoligo_heading and famoligo_content:
           updated_text += f"{famoligo_heading}\n{famoligo_content}\n\n"
        else:
            updated_text += "{{famoligö}}\n{{IPA|ipa=|audio=}}\n\n"

        if definisi_duma:
            updated_text += f"{definisi_duma}\n\n"
        else: 
            updated_text += "{{definisi}}\n\n{{duma-duma}}\n\n"

        if gambara_heading and gambara_content:
            updated_text += f"{gambara_heading}\n{gambara_content}\n\n"
        else: 
            updated_text += "{{gambara}}\n\n\n"

        if eluaha_heading and eluaha_content:
            updated_text += f"{eluaha_heading}\n{eluaha_content}\n\n"
        else: 
            updated_text += "{{eluaha}}\n* {{-id-}}:\n* {{-en-}}:\n* {{-de-}}:\n\n"

        if sinonim_heading and sinonim_content:
            updated_text += f"{sinonim_heading}\n{sinonim_content}\n\n"
        else: 
            updated_text += "{{sinonim}}\n:Lö hadöi\n\n"

        if antonim_heading and antonim_content:
            updated_text += f"{antonim_heading}\n{antonim_content}\n\n"
        else: 
            updated_text += "{{antonim}}\n:Lö hadöi\n\n"

        if etimologi_heading and etimologi_content:
            updated_text += f"{etimologi_heading}\n{etimologi_content}\n\n"
        else: 
            updated_text += "{{etimologi}}\n:Lö hadöi\n\n"

        if nitongoni_heading and nitongoni_content:
            updated_text += f"{nitongoni_heading}\n{nitongoni_content}\n\n"
        else: 
            updated_text += "{{nitöngöni}}\n:Lö hadöi\n\n"

        if fakhili_heading and fakhili_content:
            updated_text += f"{fakhili_heading}\n{fakhili_content}\n\n"
        else: 
            updated_text += "{{fakhili}}\n:Lö hadöi\n\n"

        if daha_heading and daha_content:
            updated_text += f"{daha_heading}\n{daha_content}\n\n"
        else: 
            updated_text += "{{daha}}\n:Lö hadöi\n\n"

        if fakhai_heading and fakhai_content:
            updated_text += f"{fakhai_heading}\n{fakhai_content}\n\n"
        else: 
            updated_text += "{{fakhai}}\n:Lö hadöi\n\n"
            
        if baero_heading and baero_content:
            updated_text += f"{baero_heading}\n{baero_content}\n\n"
        else: 
            updated_text += "{{baero}}\n*Lö hadöi\n\n"

        if umbu_heading and umbu_content:
            updated_text += f"{umbu_heading}\n{umbu_content}\n\n"
        else: 
            updated_text += "{{umbu}}\n*Lö hadöi\n\n"           

        if kategori:
            updated_text += f"{kategori}"

        # Return the updated text
        self.put_current(updated_text.strip(), summary=self.opt.summary)

def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process pagegenerators arguments
    local_args = gen_factory.handle_args(local_args)

    # Parse your own command line arguments
    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    gen = gen_factory.getCombinedGenerator(preload=True)

    # check if further help is needed
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        # pass generator and private options to the bot
        bot = NiaWikikamusBot(generator=gen, **options)
        bot.run()  # guess what it does


if __name__ == '__main__':
    main()
