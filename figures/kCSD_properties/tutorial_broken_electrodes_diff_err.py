import os
import numpy as np
from scipy.interpolate import griddata
from figure_properties import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec


def fetch_folder(csd_type='small'):
    if csd_type == 'small':
        all_folder = 'small_srcs_all_ele'
        all_minus_5 = 'small_srcs_minus_5'
        all_minus_10 = 'small_srcs_minus_10'
        all_minus_20 = 'small_srcs_minus_20'
    else:
        all_folder = 'large_srcs_all_ele'
        all_minus_5 = 'large_srcs_minus_5'
        all_minus_10 = 'large_srcs_minus_10'
        all_minus_20 = 'large_srcs_minus_20'
    fldrs = [all_folder, all_minus_5, all_minus_10, all_minus_20]
    fldrs = [os.path.join(os.path.abspath('.'), fs) for fs in fldrs]
    return fldrs


def load_files(folderpaths, seeds):
    list_dict = []
    for folderpath in folderpaths:
        files = [os.path.join(folderpath, str(seed)+'.npz') for seed in seeds]
        eval_dict = {}
        for f in files:
            csd_seed = os.path.basename(f)[:-4]
            eval_dict[int(csd_seed)] = np.load(f)
        list_dict.append(eval_dict)
    return list_dict


def set_axis(ax, letter=None):
    ax.text(
        -0.05,
        1.10,
        letter,
        fontsize=20,
        weight='bold',
        transform=ax.transAxes)
    return ax


def grid(x, y, z):
    x = x.flatten()
    y = y.flatten()
    z = z.flatten()
    xi, yi = np.mgrid[min(x):max(x):complex(0, 100),
                      min(y):max(y):complex(0, 100)]
    zi = griddata((x, y), z, (xi, yi), method='linear')
    return xi, yi, zi


def electrode_positions(missing_ele=0):
    # Electrode positions
    ele_x, ele_y = np.mgrid[0.05: 0.95: 10j,
                            0.05: 0.95: 10j]
    ele_pos = np.vstack((ele_x.flatten(), ele_y.flatten())).T
    # Remove some electrodes
    remove_num = missing_ele
    rstate = np.random.RandomState(42)  # just a random seed
    rmv = rstate.choice(ele_pos.shape[0], remove_num, replace=False)
    ele_pos = np.delete(ele_pos, rmv, 0)
    return ele_pos


def point_errors(true_csd, est_csd):
    true_csd_r = true_csd.reshape(true_csd.size, 1)
    est_csd_r = est_csd.reshape(est_csd.size, 1)
    epsilon = np.linalg.norm(true_csd_r)/np.max(abs(true_csd_r))
    err_r = abs(est_csd_r/(np.linalg.norm(est_csd_r)) -
                true_csd_r/(np.linalg.norm(true_csd_r)))
    err_r *= epsilon
    err = err_r.reshape(true_csd.shape)
    return err


def sigmoid_mean(error):
    sig_error = 2*(1./(1 + np.exp((-error))) - 1/2.)
    return sig_error


def point_errors_Ch(true_csd, est_csd):
    nrm_est = est_csd.reshape(est_csd.size, 1) / np.max(np.abs(est_csd))
    nrm_csd = true_csd.reshape(true_csd.size, 1) / np.max(np.abs(true_csd))
    err = np.linalg.norm(nrm_csd - nrm_est, axis=1).reshape(true_csd.shape)
    return err


def eval_errors(list_dicts, seed_list):
    list_errs = []
    for ii, ele_data in enumerate(list_dicts):
        errs = np.zeros((len(seed_list), ele_data[0]['post_cv'].shape[0],
                         ele_data[0]['post_cv'].shape[1]))
        for seed in seed_list:
            est_csd = ele_data[seed]['post_cv']
            true_csd = ele_data[seed]['true_csd']
            point_errs = point_errors(true_csd, est_csd)
            errs[seed] = point_errs
        np.save('point_err_' +str(ii) + '.npy', errs)
        err = np.mean(errs, axis=0)
        list_errs.append(err)  # average error
    return list_errs


def eval_errors_random(list_dicts, seed_list):
    list_errs = []
    for ii, ele_data in enumerate(list_dicts):
        errs = np.zeros((len(seed_list), ele_data[0]['post_cv'].shape[0],
                         ele_data[0]['post_cv'].shape[1]))
        for seed in seed_list:
            est_csd = ele_data[seed]['post_cv']
            true_csd = ele_data[seed]['true_csd']
            point_errs = point_errors(true_csd, est_csd)
            errs[seed] = point_errs
        list_errs.append(errs)  # average error
    return list_errs


def make_subplot(ax, val_type, xs, ys, values, cax, title=None, ele_pos=None,
                 xlabel=False, ylabel=False, letter='', t_max=None):
    if val_type == 'csd':
        cmap = cm.bwr
    elif val_type == 'pot':
        cmap = cm.PRGn
    else:
        cmap = cm.Greys
    ax.set_aspect('equal')
    if t_max is None:
        t_max = np.max(np.abs(values))
    levels = np.linspace(0, t_max, 16)
    im = ax.contourf(xs, ys, values,
                     levels=levels, cmap=cmap)
    if val_type != 'csd':
        ax.scatter(ele_pos[:, 0], ele_pos[:, 1], 10, c='k')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    if xlabel:
        ax.set_xlabel('X (mm)')
    if ylabel:
        ax.set_ylabel('Y (mm)')
    if title is not None:
        ax.set_title(title, pad=10)
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    ticks = np.linspace(0, t_max, 3, endpoint=True)
    plt.colorbar(im, cax=cax, orientation='horizontal', format='%.2f',
                 ticks=ticks)
    set_axis(ax, letter=letter)
    return ax, cax


def fetch_values(csd_type):
    if csd_type =='small':
        seed_list = range(100)
    else:
        seed_list = range(100)
    fldrs = fetch_folder(csd_type=csd_type)
    list_dicts = load_files(fldrs, seed_list)
    errs = eval_errors(list_dicts, seed_list)
    return errs


def fetch_values_random(csd_type):
    fldrs_s = fetch_folder(csd_type='small')
    fldrs_l = fetch_folder(csd_type='large')
    list_dicts_s = load_files(fldrs_s, range(100))
    list_dicts_l = load_files(fldrs_l, range(100))
    errs_s = eval_errors_random(list_dicts_s, range(100))
    errs_l = eval_errors_random(list_dicts_l, range(100))
    errs = []
    for ii in range(len(errs_s)):
        error = np.concatenate((errs_s[ii], errs_l[ii]))
        errs.append(np.mean(error, axis=0))
    return errs


def generate_figure():
    errs = fetch_values_random('random')
    err_max = 0.2
    csd_at = np.mgrid[0.:1.:100j,
                      0.:1.:100j]
    csd_x, csd_y = csd_at
    fig = plt.figure(figsize=(20, 18))
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.95, bottom=0.69)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, title='Error CSD', xlabel=True, ylabel=True, letter='A',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, errs[1], ele_pos=electrode_positions(missing_ele=5),
                 cax=cax, title='Error CSD 5 broken', xlabel=True,  letter='B',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, errs[2], ele_pos=electrode_positions(missing_ele=10),
                 cax=cax, title='Error CSD 10 broken', xlabel=True, letter='C',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, errs[3], ele_pos=electrode_positions(missing_ele=20),
                 cax=cax, title='Error CSD 20 broken', xlabel=True, letter='D',
                 t_max=err_max)

    errs = fetch_values('small')
    err_max = 0.2
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.63, bottom=0.37)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, xlabel=True, ylabel=True, letter='E',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, errs[1], ele_pos=electrode_positions(missing_ele=5),
                 cax=cax, xlabel=True, letter='F',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, errs[2], ele_pos=electrode_positions(missing_ele=10),
                 cax=cax, xlabel=True, letter='G',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, errs[3], ele_pos=electrode_positions(missing_ele=20),
                 cax=cax, xlabel=True, letter='H',
                 t_max=err_max)

    errs = fetch_values('large')
    err_max = 0.2
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.31, bottom=0.05)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, xlabel=True, ylabel=True, letter='I',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, errs[1], ele_pos=electrode_positions(missing_ele=5),
                 cax=cax,  xlabel=True,  letter='J',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, errs[2], ele_pos=electrode_positions(missing_ele=10),
                 cax=cax,  xlabel=True,  letter='K',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, errs[3], ele_pos=electrode_positions(missing_ele=20),
                 cax=cax,  xlabel=True,  letter='L',
                 t_max=err_max)
    plt.savefig('tutorial_electrode_loss_newRDM_test.png', dpi=300)
    #plt.show()


def generate_figure2():
    errs = fetch_values_random('random')
    err_max = np.max(abs(errs[3]-errs[0]))
    csd_at = np.mgrid[0.:1.:100j,
                      0.:1.:100j]
    csd_x, csd_y = csd_at
    fig = plt.figure(figsize=(20, 18))
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.95, bottom=0.69)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, title='Error CSD', xlabel=True, ylabel=True, letter='A',
                 t_max=.2)
    ax.text(-0.4, 0.5, 'Small+Large sources', fontsize=20, rotation=90, va='center')

    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[1] - errs[0]), ele_pos=electrode_positions(missing_ele=5),
                 cax=cax, title='5 broken - Error CSD ', xlabel=True,  letter='B',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[2] - errs[0]), ele_pos=electrode_positions(missing_ele=10),
                 cax=cax, title='10 broken - Error CSD', xlabel=True, letter='C',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[3] - errs[0]), ele_pos=electrode_positions(missing_ele=20),
                 cax=cax, title='20 broken - Error CSD', xlabel=True, letter='D',
                 t_max=err_max)

    errs = fetch_values('small')
    err_max = np.max(abs(errs[3] - errs[0]))
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.63, bottom=0.37)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, xlabel=True, ylabel=True, letter='E',
                 t_max=.2)
    ax.text(-0.4, 0.5, 'Small sources', fontsize=20, rotation=90, va='center')
    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[1] - errs[0]), ele_pos=electrode_positions(missing_ele=5),
                 cax=cax, xlabel=True, letter='F',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[2] - errs[0]), ele_pos=electrode_positions(missing_ele=10),
                 cax=cax, xlabel=True, letter='G',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[3] - errs[0]), ele_pos=electrode_positions(missing_ele=20),
                 cax=cax, xlabel=True, letter='H',
                 t_max=err_max)

    errs = fetch_values('large')
    err_max = np.max(abs(errs[3] - errs[0]))
    gs = gridspec.GridSpec(2, 4, height_ratios=[1., 0.04], width_ratios=[1]*4)
    gs.update(top=.31, bottom=0.05)
    ax = plt.subplot(gs[0, 0])
    cax = plt.subplot(gs[1, 0])
    make_subplot(ax, 'err', csd_x, csd_y, errs[0], ele_pos=electrode_positions(missing_ele=0),
                 cax=cax, xlabel=True, ylabel=True, letter='I',
                 t_max=.2)
    ax.text(-0.4, 0.5, 'Large sources', fontsize=20, rotation=90, va='center')
    ax = plt.subplot(gs[0, 1])
    cax = plt.subplot(gs[1, 1])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[1] - errs[0]), ele_pos=electrode_positions(missing_ele=5),
                 cax=cax,  xlabel=True,  letter='J',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 2])
    cax = plt.subplot(gs[1, 2])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[2] - errs[0]), ele_pos=electrode_positions(missing_ele=10),
                 cax=cax,  xlabel=True,  letter='K',
                 t_max=err_max)
    ax = plt.subplot(gs[0, 3])
    cax = plt.subplot(gs[1, 3])
    make_subplot(ax, 'err', csd_x, csd_y, abs(errs[3] - errs[0]), ele_pos=electrode_positions(missing_ele=20),
                 cax=cax,  xlabel=True,  letter='L',
                 t_max=err_max)
    plt.savefig('tutorial_electrode_loss_newRDM_diff_test.png', dpi=300)
    #plt.show()


if __name__ == '__main__':
#    generate_figure()
    generate_figure2()


