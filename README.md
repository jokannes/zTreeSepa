# zTreeSepa
This is a tool to create a SEPA XML batch payment file from zTree payment files for convenient bank transfers to lab subjects.

# Description
The zTree software for economic experiments (Fischbacher, 2007) automatically creates a payment file at the end of a lab session. The zTreeSepa tool allows manual addition of surplus participants and automatic conversion of the payment info to a SEPA XML payment file according to the pain.001.001.03 schema. 

# Usage
## Downloading the tool
You can either build the tool yourself using Python or you can download the .exe in the Releases area. For that, click on the tag at the top of the repository and download the .exe file.

## How to get a payment file from zTree
For detailed information, please refer to the zTree manual. In short, after your treatment(s), you should run a questionnaire with an address form in it. After the conclusion of the questionnaire, the payment files are automatically created.

## Setting your institution details
You can set your institution's banking details by amending the info in settings.json - this file will be generated automatically when you first run zTreeSepa. The initial data is testing data. The account you set here will be the debitor account of the payment. Specify the currency with the three-digit code according to the ISO 4217 standard. In zTreeSepa, you set the payment reference, which will be the same for each individual transaction. Specify the experiment name for documentation reasons. Note that your institution details are saved permanently in the settings.json, so that you don't have to re-enter your institution details each time you use the tool.

## Importing the payment file and adding surplus participants
Import the combo payment file into the tool (format: DATE_TIME_combo.pay - note: older zTree versions only output the .pay file - you can use that instead). You will see a preview of the data in the file, with the option to add surplus participants. You can also add a fixed amount to all payments (e.g., if you want to compensate subjects for some unforeseen event during the session). If you are happy with the preview, you can generate the SEPA payment file. This will output an XML file in the specified directory, along with a PDF containing info on all the transactions that you can sign or file away for documentation reasons.

## Getting the file to the bank
Once the SEPA file has been generated, you can directly transfer it to your bank. Depending on the setup, you can use an automatic electronic payment tool for this or you can upload the file to your online banking platform (you may have to contact your bank and ask for the option to submit XML files).

# Capabilities & Limitations
The tool supports payment files from zTree versions 4, 5 and 6. Other versions may work too, but I haven't tested them. The tool contains an automatic BIC (bank identifier code) lookup, so that your lab subjects don't need to input the BIC separately. It also contains an IBAN validation to ensure there are no erroneous IBAN entries. Note that you can only add new transactions, but you cannot amend existing rows in the preview. I may add this feature later depending on demand. So far, I have only tested it for payments within Germany. In theory, it should also work for other SEPA countries as the payment file format is highly standardised. If you have any feature requests, feel free to contact me here.

# Liability
I guess it probably goes without saying, but I don't accept any liability for any issues or erroneous transfers that happen using this tool. Please do make sure that you check your output file thoroughly before transferring it to the bank.

# References
Fischbacher, Urs. (2007). Z-Tree: Zurich Toolbox for Ready-Made Economic Experiments. Exp. Econ. 10, 171-178. Experimental Economics. 10. 171-178. 10.1007/s10683-006-9159-4.
