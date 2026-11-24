"""Build source-derived benchmark units, never call production extractors for references.

Directory columns are transcribed by an independent BeautifulSoup table read;
district/year pairs below were inspected against the original source.
Scheme facts below were checked against the official Hindi table.
Statistics are manual transcriptions of PDF page 7, not PDF extraction benchmarks.
"""
import csv
import hashlib
import html
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from agriagent.normalization import MISSING, NA, text

ROOT=Path(__file__).resolve().parents[1]

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    cases=ROOT/"eval/cases"; refs=ROOT/"eval/reference"
    cases.mkdir(parents=True,exist_ok=True); refs.mkdir(parents=True,exist_ok=True)
    index=[]
    def register(name,agent,group,language,source,locator,records):
        path=cases/name
        metadata=dict(case_id=path.stem,input="eval/cases/"+name,reference="eval/reference/"+path.stem+".json",
            agent=agent,source_group=group,language=language,checked="source_verified_by_agent_not_human",
            source=source,source_locator=locator,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            parent_sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
            benchmark_limit="source-derived fragment; development-visible source; not independent unseen document")
        write_json(refs/(path.stem+".json"),dict(records=records,evidence=metadata))
        index.append(metadata)
    source="data/raw/icar_kvk.html"
    soup=BeautifulSoup((ROOT/source).read_bytes(),"html.parser")
    table=soup.find("table"); rows=table.find_all("tr")
    checked=[("datia",2007),("ahoknagar",2007),("burhanpur",2007),("neemuch",2006),("mandla",2006),
             ("badwani",2006),("umaria",2006),("sheopur",2006),("dewas",2005),("katni",2005)]
    for i,(district,year) in enumerate(checked):
        row=rows[i+2]
        name=f"directory_{i+1:02}.html"
        (cases/name).write_text('<meta charset="utf-8"><table>'+str(rows[0])+str(row)+"</table>",encoding="utf-8")
        cells=row.find_all("td",recursive=False)
        expected=[dict(crop=NA,location=district,period=NA,variable=v,value=value,unit=u,value_kind=k) for v,value,u,k in
                  (("address",text(cells[1].get_text(" ",strip=True)),"text","text"),
                   ("host_organization",text(cells[2].get_text(" ",strip=True)),"text","text"),
                   ("sanction_year",str(year),"year","integer"))]
        register(name,"directory","Document","en",source,f"table:1/row:{i+3}",expected)
    source="data/raw/msp_scheme.html"
    table=BeautifulSoup((ROOT/source).read_bytes(),"html.parser").find("table")
    rows=table.find_all("tr")
    checked=[(0,"विभाग","खाद्य नागरिक आपूर्ति एवं उपभोक्ता संरक्षण विभाग"),
      (1,"योजना का नाम","किसानों से समर्थन मूल्य पर खाद्यान्न का उपार्जन"),
      (2,"हितग्राही मूलक है या नही","नहीं"),(3,"अधिकार क्षेत्र","राज्य प्रवर्तित योजना"),
      (7,"लाभार्थी वर्ग","भूमिधारी कृषकों"),(8,"लाभार्थी का प्रकार","किसान"),
      (9,"लाभ की श्रेणी","नगद"),(10,"योजना का क्षेत्र","Urban and Rural"),
      (15,"आवेदन शुल्क","निःशुल्क है"),(19,"ऑनलाइन आवेदन हेतु लिंक","http://mpeuparjan.nic.in")]
    for i,(ri,key,value) in enumerate(checked):
        name=f"scheme_{i+1:02}.html"
        # Retain context in a heading, never pass an expected answer to the parser.
        (cases/name).write_text('<meta charset="utf-8"><h1>योजना का नाम विभाग</h1><table>'+str(rows[ri])+"</table>",encoding="utf-8")
        record=dict(crop=NA,location=MISSING,period=MISSING,variable=key,value=value,unit="text",value_kind="text")
        register(name,"scheme","Document","hi",source,f"table:1/row:{ri+1}",[record])
    source="data/raw/mp_economic_survey.pdf"
    checked=[("wheat","2022-23","production","352.7","lakh tonnes","advance estimate"),
       ("wheat","2013-14","production","174.8","lakh tonnes","historical"),
       ("rice","2022-23","production","131.8","lakh tonnes","during this period; context sentence 1"),
       ("rice","2013-14","production","53.2","lakh tonnes","context sentence 1"),
       (NA,"2021-22","cropped_area_growth","5.46","percent","compared with 2020-21; A"),
       (NA,"2021-22","crop_production_growth","4.16","percent","compared with 2020-21"),
       (NA,"2021-22","insured_farmers_lower_bound","90","lakh farmers","more than"),
       (NA,NA,"irrigation_capacity_growth","585","percent","period not explicit in same clause"),
       (NA,"2022","irrigation_capacity_lower_bound","45","lakh hectare","more than"),
       (NA,"2025","irrigation_capacity_target","65","lakh hectare","target; not observed")]
    all_rows=[]
    for i,(crop,period,variable,value,unit,qualifier) in enumerate(checked):
        record=dict(crop=crop,location="Madhya Pradesh",period=period,variable=variable,value=value,unit=unit,
                    value_kind="decimal",qualifier=qualifier,origin_locator="page:7",origin_source=source)
        name=f"statistics_{i+1:02}.csv"
        with (cases/name).open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(record)); w.writeheader(); w.writerow(record)
        expected=dict(record,location="madhya pradesh")
        register(name,"statistics","Database","en",source,"page:7",[expected])
        all_rows.append(record)
    derived=ROOT/"data/derived/survey_agriculture_transcription.csv"; derived.parent.mkdir(exist_ok=True)
    with derived.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0])); w.writeheader(); w.writerows(all_rows)
    write_json(ROOT/"eval/case_index.json",index)
    print("Prepared",len(index),"source-derived benchmark units (not 30 independent documents)")

if __name__=="__main__": main()
