// Tagalog text -> Tinig phonemes. Must match train/tl_g2p.py exactly.
(function(root){
const ONES=["","isa","dalawa","tatlo","apat","lima","anim","pito","walo","siyam"];
const TEENS={11:"labing-isa",12:"labindalawa",13:"labintatlo",14:"labing-apat",15:"labinlima",16:"labing-anim",17:"labimpito",18:"labingwalo",19:"labinsiyam"};
const TENS={1:"sampu",2:"dalawampu",3:"tatlumpu",4:"apatnapu",5:"limampu",6:"animnapu",7:"pitumpu",8:"walumpu",9:"siyamnapu"};
const HUND={1:"isandaan",2:"dalawang daan",3:"tatlong daan",4:"apat na raan",5:"limang daan",6:"anim na raan",7:"pitong daan",8:"walong daan",9:"siyam na raan"};
const link=w=>w+("aeiou".includes(w[w.length-1])?"ng":" na");
function numTl(n){
  n=parseInt(n,10);
  if(n===0) return "sero"; if(n<10) return ONES[n]; if(TEENS[n]) return TEENS[n];
  if(n<100){ const t=Math.floor(n/10),o=n%10; return TENS[t]+(o?" at "+ONES[o]:""); }
  if(n<1000){ const h=Math.floor(n/100),r=n%100; return HUND[h]+(r?" at "+numTl(r):""); }
  if(n<1000000){ const th=Math.floor(n/1000),r=n%1000; return (th===1?"isang libo":link(numTl(th))+" libo")+(r?" at "+numTl(r):""); }
  return String(n).split("").map(d=>ONES[+d]||"sero").join(" ");
}
const MAP={"g":"ɡ","r":"ɾ","y":"j","j":"dʒ","c":"k","q":"k","x":"ks","\"":""};
function normalize(text){
  let t=text.normalize("NFC").toLowerCase();
  t=t.replace(/\d+/g,m=>" "+numTl(m)+" ");
  t=t.replace(/’/g,"'").replace(/‘/g,"'").replace(/“/g,'"').replace(/”/g,'"').replace(/—/g,", ").replace(/–/g,"-");
  t=t.replace(/(^|[^\p{L}\p{N}_])mga(?![\p{L}\p{N}_])/gu,"$1maŋa").replace(/(^|[^\p{L}\p{N}_])ng(?![\p{L}\p{N}_])/gu,"$1naŋ");
  t=t.replace(/ñ/g,"ny").replace(/ng/g,"ŋ").replace(/qu/g,"k");
  t=[...t].map(ch=>ch in MAP?MAP[ch]:ch).join("");
  t=t.replace(/[^a-zɡɾŋʒ ,.!?;:'\-]/g," ");
  return t.replace(/\s+/g," ").trim();
}
root.TinigG2P={normalize,numTl};
})(typeof self!=='undefined'?self:globalThis);
