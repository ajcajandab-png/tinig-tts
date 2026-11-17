import re, unicodedata
ONES=["","isa","dalawa","tatlo","apat","lima","anim","pito","walo","siyam"]
TEENS={11:"labing-isa",12:"labindalawa",13:"labintatlo",14:"labing-apat",15:"labinlima",16:"labing-anim",17:"labimpito",18:"labingwalo",19:"labinsiyam"}
TENS={1:"sampu",2:"dalawampu",3:"tatlumpu",4:"apatnapu",5:"limampu",6:"animnapu",7:"pitumpu",8:"walumpu",9:"siyamnapu"}
HUND={1:"isandaan",2:"dalawang daan",3:"tatlong daan",4:"apat na raan",5:"limang daan",6:"anim na raan",7:"pitong daan",8:"walong daan",9:"siyam na raan"}
def link(w): return w+("ng" if w[-1] in "aeiou" else " na")
def num_tl(n):
    n=int(n)
    if n==0: return "sero"
    if n<10: return ONES[n]
    if n in TEENS: return TEENS[n]
    if n<100:
        t,o=divmod(n,10); return TENS[t]+(" at "+ONES[o] if o else "")
    if n<1000:
        h,r=divmod(n,100); return HUND[h]+(" at "+num_tl(r) if r else "")
    if n<1000000:
        th,r=divmod(n,1000); return ("isang libo" if th==1 else link(num_tl(th))+" libo")+(" at "+num_tl(r) if r else "")
    return " ".join(ONES[int(d)] or "sero" for d in str(n))
def normalize(text):
    t=unicodedata.normalize("NFC",text).lower()
    t=re.sub(r"\d+",lambda m:" "+num_tl(m.group())+" ",t)
    t=t.replace("’","'").replace("‘","'").replace("“",'"').replace("”",'"').replace("—",", ").replace("–","-")
    t=re.sub(r"\bmga\b","maŋa",t); t=re.sub(r"\bng\b","naŋ",t)
    t=t.replace("ñ","ny").replace("ng","ŋ").replace("qu","k")
    out=[]
    for ch in t:
        out.append({"g":"ɡ","r":"ɾ","y":"j","j":"dʒ","c":"k","q":"k","x":"ks","\"":"",}.get(ch,ch))
    t="".join(out)
    t=re.sub(r"[^a-zɡɾŋʒ ,.!?;:'\-]"," ",t)
    t=re.sub(r"\s+"," ",t).strip()
    return t
if __name__=="__main__":
    for s in ["Magandang umaga sa inyong lahat!","Ang mga bata ng baryo.","May 320 na mag-aaral, 15 guro at 2026 na libro.","Niño, jeep, quezon, taxi"]:
        print(s,"->",normalize(s))
    for n in [1,11,12,14,15,19,20,25,34,40,99,100,256,1000,2026]: print(n,num_tl(n))
