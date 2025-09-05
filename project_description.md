#### Switch to a 100% cloud pattern that returns a OneDrive sharing link and surfaces a Launch button in your app.



**Azure Function (Python) code (HTTP trigger) that adds a hyperlinked TOC in-memory using PyMuPDF.**

**A Power Automate (cloud) flow build sheet (step-by-step, with copy-paste expressions).**

**Power Apps screen wiring, including a Launch(varResult.shareLink) button.**

**A short test plan \& notes.**

Power Apps + cloud flows can call HTTP endpoints and use OneDrive for Business to read/write files—no desktop machine required.Invoke an Azure Function from the flow and then save the returned PDF back to OneDrive and create a share link. \[1]\[2]





**1) Azure Function (Python) — “Add PDF TOC”**

This is the serverless piece the flow calls. It receives the PDF as Base64, inserts TOC pages based on existing PDF bookmarks, and returns the modified PDF as Base64.

Use the Python v2 programming model (decorators) and deploy on an Azure Functions (Linux) plan. \[3]

function\_app.py

\# Azure Functions (Python v2) - HTTP Trigger

import logging, json, base64

import azure.functions as func

import fitz  # PyMuPDF

app = func.FunctionApp(http\_auth\_level=func.AuthLevel.FUNCTION)

@app.function\_name(name="AddPdfToc")

@app.route(route="add-pdf-toc", methods=\["POST"])  # POST https://\&lt;app\&gt;.azurewebsites.net/api/add-pdf-toc?code=\&lt;function\_key\&gt;

def add\_pdf\_toc(req: func.HttpRequest) -\&gt; func.HttpResponse:

&nbsp;   try:

&nbsp;       body = req.get\_json()

&nbsp;       pdf\_b64 = body\["fileContent"]

&nbsp;       title = body.get("title", "Hyperlinked Table of Contents")

&nbsp;       zoom = float(body.get("zoom", 1.0))

&nbsp;       pdf\_bytes = base64.b64decode(pdf\_b64)

&nbsp;       doc = fitz.open(stream=pdf\_bytes, filetype="pdf")

&nbsp;       try:

&nbsp;           toc = doc.get\_toc(simple=False)

&nbsp;           if not toc:

&nbsp;               toc = \[\[lvl, t, p, {}] for (lvl, t, p) in doc.get\_toc()]

&nbsp;           if not toc:

&nbsp;               return func.HttpResponse(

&nbsp;                   json.dumps({"status": "ERROR", "error": "No bookmarks found in PDF. Create bookmarks first."}),

&nbsp;                   status\_code=400, mimetype="application/json")

&nbsp;           LEFT, RIGHT, TOP = 54, 54, 54

&nbsp;           LINE\_H, FS = 18, 11

&nbsp;           FONT, COLOR = "helv", (0, 0, 1)

&nbsp;           first\_rect = doc\[0].rect

&nbsp;           lines\_per = max(1, int(((first\_rect.height - 2 \* TOP)//LINE\_H) - 2))

&nbsp;           num\_toc\_pages = (len(toc) + lines\_per - 1)//lines\_per

&nbsp;           for \_ in range(num\_toc\_pages):

&nbsp;               doc.new\_page(pno=0)

&nbsp;           page\_index = 0

&nbsp;           cur = doc\[page\_index]

&nbsp;           y = TOP

&nbsp;           cur.insert\_text((LEFT, y), title, fontsize=16, fontname=FONT, fill=(0,0,0))

&nbsp;           y += 2\*LINE\_H

&nbsp;           for (lvl, title\_i, p1, \_meta) in toc:

&nbsp;               if y \&gt; cur.rect.height - TOP:

&nbsp;                   page\_index += 1

&nbsp;                   cur = doc\[page\_index]

&nbsp;                   y = TOP

&nbsp;                   cur.insert\_text((LEFT, y), f"{title} (cont.)", fontsize=14, fontname=FONT, fill=(0,0,0))

&nbsp;                   y += 2\*LINE\_H

&nbsp;               x = LEFT + max(0, (int(lvl)-1))\*14

&nbsp;               label = (title\_i or "").strip()

&nbsp;               if len(label) \&gt; 180:

&nbsp;                   label = label\[:179] + "…"

&nbsp;               cur.insert\_text((x, y), label, fontsize=FS, fontname=FONT, fill=COLOR)

&nbsp;               pn = str(int(p1))

&nbsp;               est = len(pn) \* FS \* 0.5

&nbsp;               cur.insert\_text((cur.rect.width - RIGHT - est, y), pn, fontsize=FS, fontname=FONT, fill=(0,0,0))

&nbsp;               clickable\_rect = fitz.Rect(x, y - FS, cur.rect.width - RIGHT, y + 4)

&nbsp;               target\_idx = max(0, min((int(p1) - 1) + num\_toc\_pages, doc.page\_count - 1))

&nbsp;               cur.insert\_link({

&nbsp;                   "kind": fitz.LINK\_GOTO,     # internal “GoTo” link

&nbsp;                   "from": clickable\_rect,     # clickable area

&nbsp;                   "page": target\_idx,         # 0-based target page index

&nbsp;                   "zoom": zoom                # fixed zoom (1.0=100%)

&nbsp;               })

&nbsp;               y += LINE\_H

&nbsp;           try:

&nbsp;               doc.set\_page\_labels(\[

&nbsp;                   {"startpage": 0, "prefix": "", "firstpagenum": 1, "style": "D"},

&nbsp;                   {"startpage": num\_toc\_pages, "prefix": "", "firstpagenum": 1, "style": "D"}

&nbsp;               ])

&nbsp;           except Exception:

&nbsp;               pass

&nbsp;           out\_bytes = doc.tobytes()

&nbsp;       finally:

&nbsp;           doc.close()

&nbsp;       return func.HttpResponse(

&nbsp;           json.dumps({"status": "OK", "fileContent": base64.b64encode(out\_bytes).decode("ascii")}),

&nbsp;           status\_code=200, mimetype="application/json")

&nbsp;   except Exception as e:

&nbsp;       logging.exception("TOC build failed")

&nbsp;       return func.HttpResponse(json.dumps({"status": "ERROR", "error": str(e)}), status\_code=500, mimetype="application/json")

PyMuPDF lets us create internal GoTo links via page.insert\_link({... 'kind': LINK\_GOTO ...}), specifying a clickable rectangle and target page—exactly what we use here. \[4]\[5]

requirements.txt

azure-functions

pymupdf==1.24.9

host.json

{

&nbsp; "version": "2.0"

}

Example request and response format

POST https://\&lt;your-funcapp\&gt;.azurewebsites.net/api/add-pdf-toc?code=\&lt;function\_key\&gt;

Content-Type: application/json

{

&nbsp; "fileContent": "\&lt;BASE64\_of\_source\_pdf\&gt;",

&nbsp; "title": "Hyperlinked Table of Contents",

&nbsp; "zoom": 1.0

}

{ "status": "OK", "fileContent": "\&lt;BASE64\_of\_modified\_pdf\&gt;" }

You can deploy with VS Code or Azure Functions Core Tools, then copy the Function URL (with ?code=) for use in your flow. The Python worker runs on a Linux plan in Azure. \[3]





**2) Power Automate (cloud) — Flow build sheet**

Name: Flow\_AddPdfToc\_Cloud\\ Trigger: Power Apps (V2) with two Text inputs:

sourcePath — OneDrive path like /Documents/pdf\_study/XL092002\_monthly\_tables\_pdf.pdf

outputFolder — OneDrive folder like /Documents/pdf\_study

Power Apps (V2) lets you strongly type inputs (Text/Number/…); it’s the modern trigger to call flows from apps. \[1]\[6]

Actions (in order):

OneDrive for Business – Get file content using path

File path = sourcePath (from trigger)

The OneDrive for Business connector supports Get file content using path to fetch file bytes by a OneDrive-relative path. \[7]\[2]

Compose (Name: srcBase64)

Inputs = base64(body('Getfilecontentusingpath')) (Converts the binary to Base64 for HTTP JSON.)

HTTP (to Azure Function)

Method: POST

URI: https://<your-funcapp>.azurewebsites.net/api/add-pdf-toc?code=<function\_key>

Headers: Content-Type: application/json

Body: 

{

&nbsp; "fileContent": "@{outputs('srcBase64')}",

&nbsp; "title": "Hyperlinked Table of Contents",

&nbsp; "zoom": 1.0

}

Power Automate can call any HTTP endpoint (like your Function). You’ll POST Base64 and receive Base64 back. \[8]

OneDrive for Business – Create file

Folder Path: outputFolder (from trigger)

File Name: @{last(split(triggerBody()?\['sourcePath'], '/'))} replace .pdf with \_with\_TOC.pdf (e.g., use a Compose before or inline)

File Content: base64ToBinary(body('HTTP')?\['fileContent'])

OneDrive for Business – Create share link for a file

File: (use the “Id” or “Path” dynamic value from Create file)

Link type: View

Scope: Organization

The OneDrive for Business connector includes Create share link (view or edit; org scope). Perfect for returning a link to your app users. \[2]\[9]

Respond to a PowerApp or flow

Add four Text outputs:

status = @{body('HTTP')?\['status']}

outputPath = @{outputs('Create\_file')?\['body/Path']}

shareLink = @{body('Create\_share\_link\_for\_a\_file')?\['link']\['webUrl']}

error = @{if(equals(body('HTTP')?\['status'],'OK'),'', coalesce(body('HTTP')?\['error'],'Unknown error'))}

Returning data to Power Apps via this action is the recommended pattern; then read properties off the returned object in your app. \[10]

Connector notes \& limits: The OneDrive for Business connector documents actions (get content, create file, create share link) and limitations (large files/timeouts), which may influence very large PDFs. \[2]

3\) Power Apps — Screen wiring (with Launch button)

Controls

txtSourcePath (Text input; Default: /Documents/pdf\_study/XL092002\_monthly\_tables\_pdf.pdf)

txtOutputFolder (Text input; Default: /Documents/pdf\_study)

btnCreateToc (Button: “Create Hyperlinked TOC”)

btnOpenLink (Button: “Open PDF”)

btnCreateToc.OnSelect

Set(

&nbsp;   varResult,

&nbsp;   Flow\_AddPdfToc\_Cloud.Run(

&nbsp;       {

&nbsp;           sourcePath: txtSourcePath.Text,

&nbsp;           outputFolder: txtOutputFolder.Text

&nbsp;       }

&nbsp;   )

);

If(

&nbsp;   varResult.status = "OK",

&nbsp;   Notify("TOC created", NotificationType.Success),

&nbsp;   Notify("Error: " \&amp; Coalesce(varResult.error, "Unknown error"), NotificationType.Error)

);

btnOpenLink.DisplayMode

If( IsBlankOrError(varResult.shareLink), Disabled, Edit )

btnOpenLink.OnSelect

Launch( varResult.shareLink )

The Launch function opens the OneDrive sharing URL in the user’s browser—exactly what you want for a “View PDF” experience. \[11]





**4) Test plan**

In Power Automate, run the flow manually once with test inputs:

sourcePath: /Documents/<your\_folder>/<file>.pdf

outputFolder: /Documents/<your\_folder>

Confirm the new file <file>\_with\_TOC.pdf appears in OneDrive and the first page is an inserted TOC with working links.

In Power Apps, click Create Hyperlinked TOC, then click Open PDF (Launch). It should open the share link in the browser.

Notes \& gotchas

Bookmarks are required: The TOC is created from existing PDF bookmarks (outline). If none exist, the function returns an error. (You can add bookmarks in your authoring workflow before running this.)

Org-only link: The Create share link step is set to Scope = Organization and Type = View for easy internal sharing. You can change to other scopes or link types if needed. \[2]\[9]

V2 trigger: Use Power Apps (V2) for clean, typed inputs from your app. \[1]

HTTP security: Keep the Azure Function authorization level as Function and use the ?code= URL in the flow; store it in the flow or an environment variable/connection reference per your governance. \[3]

Want me to hand you packaged assets?

I can spin up a repo/zip with:

The Azure Function app (files above: function\_app.py, requirements.txt, host.json, README.md)

A flow build guide with screenshots

A Power Apps one-pager with formulas

Or, if you have an Azure resource group already set up, I can prepare a Bicep/ARM template or VS Code launch.json/tasks.json to let you press Deploy.

Quick confirm:

Are you able to deploy an Azure Function (HTTP) in your tenant, or should I provide a ready-to-deploy zipped function + step-by-step VS Code instructions?

Do you want the flow name fixed as Flow\_AddPdfToc\_Cloud and the app screen as scrPdfToc (matches your naming pattern)?



References

\[1] Create a canvas app that can trigger a Power Automate flow

\[2] OneDrive for Business - Connectors | Microsoft Learn

\[3] Python developer reference for Azure Functions | Microsoft Learn

\[4] Link - PyMuPDF 1.26.3 documentation

\[5] Hyperlinks - Page.insert\_link - how to provide a zoomed ... - GitHub

\[6] Using Power Automate with the PowerApps V2 Trigger - 4sysops

\[7] Power Automate: OneDrive for Business - Get File Content Using Path ...

\[8] Call Azure Function From Power Automate

\[9] How To Create A Sharing Link For Files In Power Automate

\[10] Return data to PowerApps from a flow, build lists in a flow, and test a ...

\[11] Launch and Param functions - Power Platform | Microsoft Learn

