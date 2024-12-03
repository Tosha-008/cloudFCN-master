from compare_fmask_mask_defs import *
from tensorflow.keras.models import load_model

# Example usage

fmask_folder = "/media/ladmin/Vault/Fmask_masks/Splited"
norm_folder = "/media/ladmin/Vault/Splited_set_2_384"
model_path_1 = "/home/ladmin/PycharmProjects/cloudFCN-master/models/model_mfcnn_384_30_200_2.keras"
model_path_2 = '/home/ladmin/PycharmProjects/cloudFCN-master/models/model_mfcnn_384_50_200_2.keras'
model_path_3 = '/home/ladmin/PycharmProjects/cloudFCN-master/models/model_cxn_384_50_200_2.keras'

cloudiness_groups_path = "/home/ladmin/PycharmProjects/cloudFCN-master/Fmask/cloudiness_groups.pkl"  # Path to the pickle file
metrics_for_all_groups = "metrics_for_all_groups_mfcnn_3e5.json"

selected_group = "middle"  # Replace with the desired group name
max_objects = 100
dataset_name = 'Set_2'
model_name = 'cxn'

model = load_model(model_path_3, custom_objects=custom_objects)

output_file_alphas = "alpha_metrics_cxn_017_024_middle.csv"
# alpha_values = np.logspace(-12, -21, num=10, base=10)
alpha_values = np.arange(0.17, 0.24, 0.01)

results = crossval_alpha_for_group(
    pickle_file=cloudiness_groups_path,
    group_name='middle',
    fmask_folder=fmask_folder,
    norm_folder=norm_folder,
    model=model,
    model_name=model_name,
    dataset_name=dataset_name,
    alpha_values=alpha_values,
    output_file=output_file_alphas,
    max_objects=max_objects
)


# evaluate_all_groups(
#     pickle_file=cloudiness_groups_path,
#     fmask_folder=fmask_folder,
#     norm_folder=norm_folder,
#     model=model,
#     model_name=model_name,
#     dataset_name=dataset_name,
#     output_file=metrics_for_all_groups,
#     max_objects=max_objects
# )
#
# print("Analysis complete. Results saved to", metrics_for_all_groups)


# metrics = evaluate_metrics_for_group(
#     pickle_file=cloudiness_groups_path,
#     fmask_folder=fmask_folder,
#     norm_folder=norm_folder,
#     model=model,
#     model_name=model_name,
#     group_name='low',
#     dataset_name=dataset_name,
#     max_objects=1
# )


# display_images_for_group(fmask_folder,
#                          norm_folder,
#                          model=model,
#                          model_name=model_name,
#                          dataset_name=dataset_name,
#                          group_name='middle',
#                          num_images=10,
#                          pickle_file=cloudiness_groups_path) # 'low', 'middle', 'high', 'only clouds', 'no clouds', 'no filter'

# output_file_path = "cloudiness_groups.pkl"
# split_images_by_cloudiness(norm_folder, output_file_path, dataset_name='Set_2',
#                            mask_storage='/home/ladmin/PycharmProjects/cloudFCN-master/Fmask/norm_subfolders.pkl')
