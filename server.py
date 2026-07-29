from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, math, json, uuid
from pathlib import Path

BASE=Path(__file__).resolve().parent
DB=BASE/'data'/'geobancas.db'
UPLOADS=BASE/'uploads'
app=Flask(__name__, static_folder='static', static_url_path='/static')

def db():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def clean(v): return (v or '').strip()

@app.get('/')
def home(): return send_from_directory(BASE,'index.html')

@app.get('/api/stats')
def stats():
    c=db(); q=c.cursor()
    total=q.execute('select count(*) n from bancas').fetchone()['n']
    valid=q.execute("select count(*) n from bancas where latitud between 17 and 20.5 and longitud between -73 and -67").fetchone()['n']
    regulated=q.execute("select count(*) n from bancas where upper(regulada)='SI'").fetchone()['n']
    duplicates=q.execute("select count(*) n from bancas where dup_codigo='SI' or dup_coordenada='SI'").fetchone()['n']
    provinces=q.execute("select count(distinct provincia) n from bancas where provincia<>''").fetchone()['n']
    c.close()
    return jsonify(total=total,valid=valid,invalid=total-valid,regulated=regulated,unregulated=total-regulated,duplicates=duplicates,provinces=provinces)

@app.get('/api/options')
def options():
    c=db(); q=c.cursor()
    provinces=[r[0] for r in q.execute("select distinct provincia from bancas where provincia<>'' order by provincia")]
    municipalities=[r[0] for r in q.execute("select distinct municipio from bancas where municipio<>'' order by municipio")]
    concessionaires=[r[0] for r in q.execute("select distinct concesionaria from bancas where concesionaria<>'' order by concesionaria")]
    c.close(); return jsonify(provinces=provinces,municipalities=municipalities,concessionaires=concessionaires)

@app.get('/api/bancas')
def bancas():
    where=["latitud between 17 and 20.5", "longitud between -73 and -67"]
    args=[]
    mapping={'provincia':'provincia','municipio':'municipio','regulada':'regulada','concesionaria':'concesionaria'}
    for k,col in mapping.items():
        v=clean(request.args.get(k))
        if v: where.append(f'{col}=?'); args.append(v)
    search=clean(request.args.get('q'))
    if search:
        where.append('(id like ? or codigo_punto like ? or nombre_banca like ? or propietario like ? or direccion like ?)')
        s=f'%{search}%'; args += [s]*5
    bbox=clean(request.args.get('bbox'))
    if bbox:
        try:
            w,s,e,n=map(float,bbox.split(',')); where += ['longitud between ? and ?','latitud between ? and ?']; args += [w,e,s,n]
        except: pass
    limit=min(max(int(request.args.get('limit',5000)),1),10000)
    sql=f'''select id,codigo_punto,nombre_banca,propietario,regulada,provincia,municipio,sector,direccion,latitud,longitud,dup_codigo,dup_coordenada,requiere_geocodificacion
            from bancas where {' and '.join(where)} limit ?'''
    args.append(limit)
    c=db(); rows=[dict(r) for r in c.execute(sql,args)]; c.close()
    return jsonify(items=rows,count=len(rows),limit=limit,truncated=len(rows)>=limit)

@app.get('/api/bancas/<bid>')
def banca(bid):
    c=db(); row=c.execute('select * from bancas where id=?',(bid,)).fetchone()
    audit=[dict(r) for r in c.execute('select * from auditoria where banca_id=? order by id desc limit 30',(bid,))]
    c.close()
    if not row: return jsonify(error='No encontrada'),404
    return jsonify(item=dict(row),audit=audit)

@app.post('/api/bancas/<bid>/location')
def update_location(bid):
    data=request.get_json(force=True); lat=float(data['latitud']); lng=float(data['longitud'])
    if not (17<=lat<=20.5 and -73<=lng<=-67): return jsonify(error='Coordenadas fuera del rango esperado de República Dominicana'),400
    c=db(); old=c.execute('select latitud,longitud from bancas where id=?',(bid,)).fetchone()
    if not old: c.close(); return jsonify(error='No encontrada'),404
    c.execute("update bancas set latitud=?,longitud=?,estado_coordenada='CORREGIDA_MANUAL',estado_validacion='PENDIENTE_SUPERVISOR' where id=?",(lat,lng,bid))
    c.execute("insert into auditoria(banca_id,accion,campo,valor_anterior,valor_nuevo) values (?,?,?,?,?)",(bid,'ACTUALIZAR_UBICACION','coordenadas',f"{old['latitud']},{old['longitud']}",f'{lat},{lng}'))
    c.commit(); c.close(); return jsonify(ok=True)

@app.get('/api/config-distancias')
def get_distances():
    c=db(); rows=[dict(r) for r in c.execute('select * from configuracion_distancias order by categoria')]; c.close(); return jsonify(items=rows)

@app.post('/api/import-preview')
def import_preview():
    if 'file' not in request.files: return jsonify(error='Falta el archivo'),400
    f=request.files['file']; ext=Path(f.filename).suffix.lower()
    if ext not in {'.csv','.xlsx','.xls'}: return jsonify(error='Formato no admitido'),400
    name=f"{uuid.uuid4().hex}_{Path(f.filename).name}"; path=UPLOADS/name; f.save(path)
    try:
        import pandas as pd
        df=pd.read_csv(path,nrows=1000) if ext=='.csv' else pd.read_excel(path,nrows=1000)
        return jsonify(ok=True,filename=f.filename,columns=list(df.columns),sample_rows=len(df),message='Archivo recibido para revisión. No sustituyó la base actual.')
    except Exception as e: return jsonify(error=str(e)),400

if __name__=='__main__':
    app.run(host='127.0.0.1',port=8765,debug=False)
