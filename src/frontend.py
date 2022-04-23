import os
import sys

from .backend import get_groups_and_layers, generate_bears

import PySimpleGUI as sg

sg.theme('Reddit')

try:
    # For a pyinstaller single-file executable
    ICON_IMAGE = os.path.join(sys._MEIPASS, "bear_icon.ico")
    print(f'Found the icon image in the executable bundle.')
except:
    try:
        ICON_IMAGE = os.path.join(os.path.dirname(__file__), "bear_icon.ico")
    except Exception as exc:
        print(f'Could not locate icon image Error Code:\n{exc}')


def MainMenu():
    layout = [
        [sg.Text('Upload the .psd file', size=(25, 2)),
         sg.FileBrowse(key='--DATA--')],
        [sg.Text()],
        [sg.Text('Generated Image Count:', size=(25, 1)), sg.Input('', key="--IMAGECOUNT--", size=(7, 1))],
        [sg.Text()],
        [sg.Text('Max Generation Retries:', size=(25, 1)), sg.Input('100', key="--RETRIES--", size=(7, 1))],
        [sg.Text()],
        [sg.Text('Background Layer Identifier:', size=(25, 1))],
        [sg.Input('', key="--BGLAYER--", size=(35, 1))],
        [sg.Text()],
        [sg.Checkbox('Enable Layer Rarity', key='--RARITIESCHECKBUTTON--', size=(20, 1)),
         sg.Button('Set Rarities')],
        [sg.Text()],
        [sg.Text("Operation Output Folder:", size=(25, 3)),
         sg.FolderBrowse(key='--DOWNLOAD--')],
        [sg.Button('Generate Images', size=(15, 1)), sg.Button('Open Output Folder', size=(16, 1))],
        [sg.Text('', key='--NOTIFICATION--')]
    ]
    window = sg.Window('NFT Creation Tool', layout, font=("Arial", 18), icon=ICON_IMAGE)
    probabilities = None
    while True:
        event, values = window.read()
        if event == "Quit" or event == sg.WIN_CLOSED or event == "Exit":
            break
        elif event == "Open Output Folder":
            target_folder = values['--DOWNLOAD--']
            os.startfile(target_folder)
        elif event == "Set Rarities":
            # Open PS session and get all groups and layers
            path = values['--DATA--']
            print("Input File:", path)
            name, extension = os.path.splitext(path)
            if extension != ".psd":
                PopupError(f"Please upload a .psd file.")
                ext_valid = False
            else:
                ext_valid = True

            if ext_valid:
                print('Starting Photoshop and fetching the names of the groups and layers...')
                rarities_result = RarityMenu(get_groups_and_layers(path))
                if rarities_result is not None:
                    probabilities = rarities_result
                    window['--NOTIFICATION--'].update('ALERT: Rarity Preferences Saved!')

        elif event == "Generate Images":
            # validate and save input file
            path = values['--DATA--']
            print("Input File:", path)
            img_count = values['--IMAGECOUNT--']
            print("Image Count:", img_count)
            max_retries = values['--RETRIES--']
            print("Max Retries:", max_retries)
            bg_layer = values['--BGLAYER--']
            print("Background Layer ID:", bg_layer)
            target_folder = values['--DOWNLOAD--']
            print("Target Folder:", target_folder)
            name, extension = os.path.splitext(path)

            # User Input Validation:
            if extension != ".psd":
                PopupError(f"Please upload a .psd file.")
                ext_valid = False
            else:
                ext_valid = True
            try:
                img_count = int(img_count)
                img_count_valid = True
            except ValueError:
                PopupError(f"The image count must be an integer > 0.")
                img_count_valid = False
            try:
                max_retries = int(max_retries)
                max_retries_valid = True
            except ValueError:
                PopupError(f"The max retries must be an integer > 0.")
                max_retries_valid = False
            if len(bg_layer) > 0:
                bg_layer_valid = True
            else:
                PopupError(f"Please enter the group name for\nthe background layer in Photoshop.")
                bg_layer_valid = False
            if len(target_folder) > 1:
                target_folder_valid = True
            else:
                PopupError(f"Please select a target folder to export images and data.")
                target_folder_valid = False

            # If user inputs are validated, run program.
            if ext_valid and img_count_valid and max_retries_valid and bg_layer_valid and target_folder_valid:
                print('User input validation successful.')
                if values['--RARITIESCHECKBUTTON--']:
                    print('Starting Operation WITH Rarities...')
                    generation_result = generate_bears(psd_file=path, image_count=img_count,
                                                       max_generation_retries=max_retries, output_loc=target_folder,
                                                       bg_group_name=bg_layer, probabilities=probabilities)
                else:
                    print('Starting Operation WITHOUT Rarities...')
                    generation_result = generate_bears(psd_file=path, image_count=img_count,
                                                       max_generation_retries=max_retries, output_loc=target_folder,
                                                       bg_group_name=bg_layer)

                if generation_result:
                    sg.Popup(f"Image Creation Successful! File(s) saved to:\n\n{target_folder}",
                             title="OPERATION SUCCESSFUL", icon=ICON_IMAGE, font=('Arial', 12))
                else:
                    PopupError('An error occurred in the operation.\nImage creation failure. See the console.')


def RarityMenu(groups_and_layers_data: dict):
    # report_dict = groups_and_layers_data
    report_dict = {}
    for group_index, data in enumerate(groups_and_layers_data.items()):
        group, layers_list = data[0], data[1]

        last_group = True if group_index + 1 == len(groups_and_layers_data.items()) else False
        if last_group:
            print('LAST GROUP')

        layout = [
            [sg.Text(f'Enter the probabilities for the layers in the "{group}" group.\n'
                     f'(All values must add up to 100%) (Enter 0 or leave blank for 0% chance):')]
        ]

        # for layer in layer_group.artLayers:
        #     if ui_index > 10:
        #         column += 1
        #         ui_index = 0
        #         layout.append([sg.Text(f'{layer.name}:'), sg.Input(key=f'--{layer.name}--', size=(12, 1))])
        #     else:
        #         layout[ui_index].append(sg.Text(f'{layer.name}:'))
        #         layout[ui_index].append(sg.Input(key=f'--{layer.name}--', size=(12, 1)))

        # test_list = [f"{num}" for num in range(1, 31)]

        ui_index = 1
        in_columns = False
        for layer in layers_list:
            sg_text = sg.Text(f'{layer}:', size=(14, 2), justification='right')
            sg_input = sg.Input(key=f'--{layer}--', size=(11, 1))

            if ui_index > 10:
                in_columns = True
            if in_columns:
                if ui_index > 10:
                    ui_index = 1
                layout[ui_index].append(sg_text)
                layout[ui_index].append(sg_input)
                ui_index += 1
            else:
                layout.append([sg_text, sg_input])
                ui_index += 1

        if not last_group:
            layout.append([sg.Button('Next Group', size=(12, 1)), sg.Button('Check Total', size=(12, 1)),
                           sg.Text('', key="--PROBTOTAL--")])
        else:
            layout.append([sg.Button('Finish', size=(12, 1)), sg.Button('Check Total', size=(12, 1)),
                           sg.Text('', key="--PROBTOTAL--")])

        window = sg.Window(f'Set "{group}" Probabilities', layout, modal=True, icon=ICON_IMAGE,
                           font=("Arial", 12))
        while True:
            c_event, c_values = window.read()
            if c_event == "Exit" or c_event == sg.WIN_CLOSED:
                return None
            elif c_event == "Next Group" or c_event == "Finish":
                try:
                    all_entries = {
                        layer: {"chance": round(float(c_values[f"--{layer}--"].strip()), 6), "index": i + 1} if len(
                            c_values[f"--{layer}--"]) > 0 else {"chance": 0, "index": i + 1} for i, layer in
                        enumerate(layers_list)}
                    # print(all_entries)
                    try:
                        # Add zeroes
                        all_entries['Null (No Layer)']['index'] = 0
                        if sum([data['chance'] for key, data in all_entries.items()]) == 100.0:
                            report_dict[group_index] = all_entries
                            print(f'Saved rarity preferences for group: {group}')
                            if last_group:
                                window.close()
                                return report_dict
                            else:
                                break
                        else:
                            PopupError('The entries to not add up to 100.')
                    except Exception as e:
                        PopupError(f'Could not save rarity preferences.\nError Code {e}')
                except ValueError:
                    PopupError('Please enter only integer or decimal values for the probabilities.')

            elif c_event == "Check Total":
                try:
                    all_entries = [
                        round(float(c_values[f"--{layer}--"].strip()), 6) if len(c_values[f"--{layer}--"]) > 0 else 0
                        for layer
                        in layers_list]
                    window['--PROBTOTAL--'].update(f"Probabilities add up to: {sum(all_entries)}")
                except ValueError:
                    PopupError('Please enter only integer or decimal values for the probabilities.')

        window.close()


def PopupError(message: str):
    sg.PopupError(message, title='ERROR', font=("Arial", 12), icon=ICON_IMAGE)
