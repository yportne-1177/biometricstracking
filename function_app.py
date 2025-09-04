import logging, json, base64
import azure.functions as func
import fitz  # PyMuPDF

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="AddPdfToc")
@app.route(route="add-pdf-toc", methods=["POST"])
def add_pdf_toc(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        pdf_b64 = body["fileContent"]
        title = body.get("title", "Hyperlinked Table of Contents")
        zoom = float(body.get("zoom", 1.0))

        pdf_bytes = base64.b64decode(pdf_b64)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            toc = doc.get_toc(simple=False)
            if not toc:
                toc = [[lvl, t, p, {}] for (lvl, t, p) in doc.get_toc()]
            if not toc:
                return func.HttpResponse(
                    json.dumps({"status": "ERROR", "error": "No bookmarks found in PDF. Create bookmarks first."}),
                    status_code=400, mimetype="application/json")

            LEFT, RIGHT, TOP = 54, 54, 54
            LINE_H, FS = 18, 11
            FONT, COLOR = "helv", (0, 0, 1)

            first_rect = doc[0].rect
            lines_per = max(1, int(((first_rect.height - 2 * TOP)//LINE_H) - 2))
            num_toc_pages = (len(toc) + lines_per - 1)//lines_per

            for _ in range(num_toc_pages):
                doc.new_page(pno=0)

            page_index = 0
            cur = doc[page_index]
            y = TOP
            cur.insert_text((LEFT, y), title, fontsize=16, fontname=FONT, fill=(0,0,0))
            y += 2*LINE_H

            for (lvl, title_i, p1, _meta) in toc:
                if y > cur.rect.height - TOP:
                    page_index += 1
                    cur = doc[page_index]
                    y = TOP
                    cur.insert_text((LEFT, y), f"{title} (cont.)", fontsize=14, fontname=FONT, fill=(0,0,0))
                    y += 2*LINE_H

                x = LEFT + max(0, (int(lvl)-1))*14
                label = (title_i or "").strip()
                if len(label) > 180:
                    label = label[:179] + "…"

                cur.insert_text((x, y), label, fontsize=FS, fontname=FONT, fill=COLOR)
                pn = str(int(p1))
                est = len(pn) * FS * 0.5
                cur.insert_text((cur.rect.width - RIGHT - est, y), pn, fontsize=FS, fontname=FONT, fill=(0,0,0))

                clickable_rect = fitz.Rect(x, y - FS, cur.rect.width - RIGHT, y + 4)
                target_idx = max(0, min((int(p1) - 1) + num_toc_pages, doc.page_count - 1))
                cur.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "from": clickable_rect,
                    "page": target_idx,
                    "zoom": zoom
                })
                y += LINE_H

            try:
                doc.set_page_labels([
                    {"startpage": 0, "prefix": "", "firstpagenum": 1, "style": "D"},
                    {"startpage": num_toc_pages, "prefix": "", "firstpagenum": 1, "style": "D"}
                ])
            except Exception:
                pass

            out_bytes = doc.tobytes()
        finally:
            doc.close()

        return func.HttpResponse(
            json.dumps({"status": "OK", "fileContent": base64.b64encode(out_bytes).decode("ascii")}),
            status_code=200, mimetype="application/json")
    except Exception as e:
        logging.exception("TOC build failed")
        return func.HttpResponse(json.dumps({"status": "ERROR", "error": str(e)}), status_code=500, mimetype="application/json")
