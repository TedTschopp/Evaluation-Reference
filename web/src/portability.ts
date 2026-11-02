import type {Distribution} from './types';

// Only explicitly selected origins receive embedded height messages.
export function parentOrigin(search:string):string|null {
 const value=new URLSearchParams(search).get('parent_origin');
 if(!value)return null;
 try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&url.origin===value?value:null;}catch{return null;}
}
export function embedCode(href:string,parent:string):string {
 const url=new URL('./',href);url.searchParams.set('embed','1');
 const origin=parentOrigin('?parent_origin='+encodeURIComponent(parent));
 if(origin)url.searchParams.set('parent_origin',origin);
 const safe=url.href.replaceAll('&','&amp;').replaceAll('"','&quot;');
 return `<iframe src="${safe}" title="AI evaluation lab" width="100%" height="1100" loading="lazy" style="border:0"></iframe>`;
}
export function validateDistribution(value:Distribution):Distribution {
 const relative=(href:string)=>/^\.\/[a-zA-Z0-9/_.-]+$/.test(href)&&!href.split('/').includes('..');
 if(value.schema_version!=='1.0'||!Array.isArray(value.downloads)||value.downloads.some(d=>!['python','react'].includes(d.edition)||!relative(d.href))||(value.checksums&&!relative(value.checksums)))throw Error('The download catalogue must use local relative paths.');
 return value;
}
