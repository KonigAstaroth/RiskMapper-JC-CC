from django.shortcuts import redirect
from app.core.auth.firebase_config import db
from google.cloud import firestore
import datetime
from datetime import timezone, datetime
import uuid


def getUnits(request):
    uid = request.session.get('uid')
    user_ref = db.collection('Usuarios').document(uid)
    doc = user_ref.get()
    units = []
    if doc.exists:
        data = doc.to_dict()
        unit_maps = data.get('unidades',{})

        for unit_id , unit_data in unit_maps.items():
            if unit_data.get("status") == True:
                status = "Activo"
            else:
                status = "Inactivo"
            units.append({
                "id": unit_id,
                "name": unit_data.get("name"),
                "location": unit_data.get("location"),
                "description": unit_data.get("description"),
                "lastAccess": unit_data.get("lastAccess"),
                "status": status,
                # "company": unit_data.get("company")
            })
    return units

def addUnit(request):
    uid = request.session.get('uid')
    if request.method == 'POST':
        name = request.POST.get('unitName')
        location = request.POST.get('unitLocation')
        desc = request.POST.get('unitDescription')
        now = datetime.now(timezone.utc)
        unidad_id = str(uuid.uuid4())
        newUnit = {
            "name": name,
            "location": location,
            "description": desc,
            "status": True,
            "lastAccess":now,
            # "company": request.session.get('company')
        }
        user_ref= db.collection('Usuarios').document(uid)

        doc = user_ref.get()
        if doc.exists:
            user_ref.update({
                f"unidades.{unidad_id}": newUnit
            })
        else:
           user_ref.set({
                f"unidades.{unidad_id}": newUnit
            }) 
    return redirect('userSettings')


def editUnit(request, id):
    uid = request.session.get('uid')
    updates = {}
    if request.method == 'POST':
        if unitName_edit:= request.POST.get('unitName_edit'):
            updates['name_unit'] = unitName_edit
        if unitArea_edit:= request.POST.get('unitArea_edit'):
            updates['area_unit'] = unitArea_edit
        if unitDescription_edit:= request.POST.get('unitDescription_edit'):
            updates['description_unit'] = unitDescription_edit
        if status:= request.POST.get('status'):
            if status == 'true':
                updates['status'] = True
            if status == 'false':
                updates['status'] = False
    if updates:
        now = datetime.now(timezone.utc)
        user_ref= db.collection('Usuarios').document(uid)
        updates['lastAccess'] = now
        user_ref.update({
            f"unidades.{str(id)}": updates
        })
    return redirect('userSettings')

def deleteUnit(request, id):
    uid = request.session.get('uid')
    user_ref = db.collection('Usuarios').document(uid)
    user_ref.update({
        f"unidades.{str(id)}": firestore.DELETE_FIELD
    })
    return redirect('userSettings')

def getUnitSelected(uid, id):
    unit_full = None
    if id == 'None':
        unit_full = "Ninguna unidad seleccionada"
    else:
        user_ref = db.collection('Usuarios').document(uid).get()

        if user_ref.exists:
            units = user_ref.to_dict().get('unidades', {})
            unit_data = units.get(id)
            if unit_data:
                unit_full = f"Unidad de negocio seleccionada, nombre: {unit_data.get("name")}, ubicación: {unit_data.get("lcoation")}, descripción: {unit_data.get("description")}."
    return unit_full