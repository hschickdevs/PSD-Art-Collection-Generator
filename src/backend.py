import os
import sys
from random import randint
from math import prod
from time import time
import csv

import photoshop as ps
from photoshop import Session
import numpy as np


def hide_all_layers(layers):
    for layer in layers:
        layer.visible = False


def get_groups_and_layers(psd_file) -> dict:
    """Returns a dictionary with the group names as pairs and a list of their layer names"""
    with Session(psd_file, action="open") as ps:
        doc = ps.active_document
        data = {group.name: [layer.name for layer in group.artLayers] for group in doc.layerSets}

        # Account for null values
        for group, layers in data.items():
            data[group].append("Null (No Layer)")

        return data


def generate_bears(psd_file, output_loc, image_count, max_generation_retries, bg_group_name, probabilities=None):
    print('\nStarting Photoshop Application...')
    created_bears = []
    with Session(psd_file, action="open") as ps:
        abs_start = time()
        doc = ps.active_document
        options = ps.PNGSaveOptions()
        save_path = os.path.join(output_loc, "Generated_NFT_Images")
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # Make all layers outside of the layer groups persist:
        # doc.artLayers[0].visible = True
        for layer in doc.artLayers:
            layer.visible = True

        # CSV SETUP:
        csv_columns = ['filename']
        export_dict_data = []
        csv_folder_location = os.path.join(output_loc, "Exported_CSV_Data")
        if not os.path.exists(csv_folder_location):
            os.makedirs(csv_folder_location)

        print(f'Operation Information:')
        for group in doc.layerSets:
            print(f"Group '{group.name}' has {len(group.artLayers)} layers.")
            for layer in group.artLayers:
                if layer.name not in csv_columns:
                    csv_columns.append(layer.name)

        print('Calculating total combinations possible...')
        group_sizes = [len(group.artLayers) + 1 for group in
                       doc.layerSets]  # add the +1 to the len to account for the 0's
        total_combinations_possible = prod(group_sizes)
        print('Total combinations possible:', total_combinations_possible)

        if image_count <= total_combinations_possible:  # Start the operation

            start = time()
            print(
                f'\nGenerating {image_count} images out of the {total_combinations_possible} possible combinations...\n')

            mainloop = True
            if mainloop:
                for bear_num in range(image_count):
                    # Main loop for randomization algorithm
                    retry_count = 0
                    while True:
                        if retry_count <= max_generation_retries:
                            # Random generation algorithm (single line :-O):
                            if probabilities is None:
                                generated_bear = {i: randint(0,
                                                             len(group.artLayers)) if group.name.strip() != bg_group_name.strip() else randint(
                                    1, len(group.artLayers)) for i, group in enumerate(doc.layerSets)}
                            else:
                                generated_bear = {group_id: probabilities[group_id][
                                    np.random.choice([layer_name for layer_name, layer_data in group_data.items()],
                                                     p=[layer_data['chance'] / 100 for layer_name, layer_data in
                                                        group_data.items()])]['index'] for group_id, group_data in
                                                  probabilities.items()}
                            # print(generated_bear)
                            if generated_bear not in created_bears:
                                created_bears.append(generated_bear)
                                print(f'Generated image code #{bear_num + 1} in {retry_count + 1} attempt(s).\n'
                                      f'{generated_bear}')
                                break
                            else:
                                retry_count += 1
                                continue
                        else:
                            print(
                                f'Generation retry count has exceeded {max_generation_retries} for bear {bear_num + 1}.\n'
                                'Shutting down the program to conserve resources.')
                            return False

                print(f'Successfully generated {len(created_bears)} image codes in {round(time() - start, 2)} seconds.')
                # return created_bears

                print(f'\nNow attempting to export {len(created_bears)} images from the image codes...')
                start = time()
                for image_num, code_dict in enumerate(created_bears):
                    export_dict = {}
                    try:
                        print(f'\r{len(created_bears) - (image_num + 1)} Images Left | Estimated Time Remaining: {round(((time() - start) / (image_num + 1)) * (len(created_bears) - (image_num + 1)), 2)} seconds', end="")
                    except ZeroDivisionError:
                        pass

                    # For CSV Saving:
                    export_dict['filename'] = f'NFT_{image_num + 1}'
                    for column in csv_columns[1:]:
                        export_dict[column] = ""

                    for group_id, layer_id in code_dict.items():
                        doc.layerSets[group_id].visible = True
                        hide_all_layers(doc.layerSets[group_id].artLayers)
                        if layer_id != 0:
                            doc.layerSets[group_id].artLayers[layer_id].visible = True
                            export_dict[doc.layerSets[group_id].artLayers[layer_id].name] = "x"

                    export_dict_data.append(export_dict)

                    doc.saveAs(os.path.join(save_path, f'NFT_{image_num + 1}'), options)
                print(f'\nSuccessfully exported {len(created_bears)} codes to images in {round(time() - start, 2)} seconds.')
                print(f'\nExporting CSV...')
                with open(os.path.join(csv_folder_location, "data.csv"), 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns, lineterminator="\n")
                    writer.writeheader()
                    for data in export_dict_data:
                        writer.writerow(data)
                    print('Successfully Saved Data to CSV.')

                print('\nOperation completed! All files can be found in the specified directory.\n'
                      f'Total Program Runtime: {round(time() - start, 3)} seconds.')
                return True

        else:
            print(
                f'\nUnable to perform the operation due to the fact that the requested image count ({image_count}) is greater than the number of possible combinations ({total_combinations_possible}).')
            return False
