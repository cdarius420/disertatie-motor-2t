# importa_parametri.py - script Fusion
# Citește parametri_fusion.csv (scris de s07_export_fusion.m) și creează sau
# actualizează User Parameters în designul deschis.
# Parametrii existenți își păstrează numele; li se schimbă expresia și comentariul.
#
# Instalare: în Fusion, Utilities > Add-Ins > Scripts and Add-Ins,
# Create > Script, Python, nume importa_parametri; înlocuiești codul generat
# cu acest fișier, salvezi și apeși Run.

import csv
import traceback

import adsk.core
import adsk.fusion


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('Deschide un design în Fusion înainte de import.')
            return

        dialog = ui.createFileDialog()
        dialog.title = 'Alege parametri_fusion.csv'
        dialog.filter = 'CSV (*.csv)'
        if dialog.showOpen() != adsk.core.DialogResults.DialogOK:
            return

        params = design.userParameters
        noi, actualizati, erori = 0, 0, []
        with open(dialog.filename, newline='', encoding='utf-8-sig') as f:
            for rand in csv.DictReader(f):
                nume = rand['Nume']
                unitate = rand['Unitate']
                expresie = rand['Expresie']
                comentariu = rand['Comentariu']
                try:
                    p = params.itemByName(nume)
                    if p:
                        p.expression = expresie
                        p.comment = comentariu
                        actualizati += 1
                    else:
                        params.add(nume, adsk.core.ValueInput.createByString(expresie),
                                   unitate, comentariu)
                        noi += 1
                except Exception:
                    erori.append(nume)

        mesaj = 'Parametri noi: {}; actualizați: {}.'.format(noi, actualizati)
        if erori:
            mesaj += '\nNu s-au putut scrie: ' + ', '.join(erori)
        ui.messageBox(mesaj)
    except Exception:
        if ui:
            ui.messageBox('Eroare:\n{}'.format(traceback.format_exc()))
