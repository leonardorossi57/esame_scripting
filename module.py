import numpy as np
import pandas as pd
from scipy.fft import fft, ifft, fftshift, ifftshift
from scipy.optimize import curve_fit, minimize
import plotly.express as px
import json

# Funzioni per fit
def Ipl(y, B, sw, sd, wl, d):
    return sw * np.sinc(B * sw * (y + sd / 2) / (wl * d))
def Imi(y, B, sw, sd, wl, d):
    return sw * np.sinc(B * sw * (y - sd / 2) / (wl * d))

def fit_up(y, vis, A, B, sw, sd, wl, d, ai): 
    return A * ai * ((Ipl(y, B, sw, sd, wl, d) ** 2 + Imi(y, B, sw, sd, wl, d) ** 2) + 2 * vis * Ipl(y, B, sw, sd, wl, d) * Imi(y, B, sw, sd, wl, d))
def fit_down(y, vis, A, B, sw, sd, wl, d, ai): 
    return A * ai * ((Ipl(y, B, sw, sd, wl, d) ** 2 + Imi(y, B, sw, sd, wl, d) ** 2) - 2 * vis * Ipl(y, B, sw, sd, wl, d) * Imi(y, B, sw, sd, wl, d))

def generate_speckle_field(source_size, dist, scatt_num, wavelen): # Use, for the first field, a "monte carlo" method
    """ Generate a numpy array containing a one-dimensional speckle field using a monte carlo randomization
    Arguments:
        source_size: size of the source line in [cm]
        dist: distance from the source of the field to the screen on which it appears in [cm]
        scatt_num: number of source points in the source line
        wavelen: wavelength of the light in [nm]
    Returns:
        (field, screen): tuple of a numpy array containing the speckle field and a numpy array containing the coordinates of the points on the screen in [cm]
    """

    # corr = corr / 1e4 # Convert lengths to cm

    wavelen = wavelen / 1e7 # convert to cm
    corr = 0

    screen_size = 30 # [cm] (section of the beam under analysis)
    dx = 0.005 # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays
    field = np.zeros(dim, dtype = complex) # Array containing the speckle field
    screen = np.linspace(-screen_size/2, screen_size/2, dim)

    if corr == 0:
        # If there is no correlation length in the source, extract random points on the source area and add a spherical wave for each of them. The 
        # resulting sum is the speckle field.
        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle)
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen)/np.sqrt(1 + (scatt - screen) ** 2/dist ** 2) 
    else:
        # If there is a nonzero correlation length, the wave from each scatterer is profiled by an Airy disc (or maybe a gaussian function is better). 
        # The sum and the speckle field are calculated in the same way as above

        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle) with gaussian profile. This has not been tested yet.
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen) * np.exp(-((screen - scatt) * corr) ** 2)/np.sqrt(1 + (scatt - screen) ** 2 / dist ** 2)
    
    field = field/scatt_num
    # return the array with the field 
    return field, screen

def filter(filter_type, field, filter_width, screen_size, dx):
    """ Execute spatial filtering on a 1D speckle field using fast fourier transform
    Arguments: 
        filter_type: a string, either 'Gaussian' or 'Rectangular', determines the type of filtering
        field: numpy array containing the speckle field to be filtered
        filter_width: width of the spectrum resulting from the filtering
    Returns:
        filt_field: numpy array containing the filtered field
    """
        
    kspace_size = 2 * np.pi/dx
    dk = 2 * np.pi/screen_size
    dim = int(kspace_size/dk) + 1 # Dimension of the arrays
    kspace = np.linspace(-kspace_size / 2, kspace_size / 2, dim)

    # This functions just performs a FFT, profiles the spectrum with the appropriate function (step or gaussian) and then IFFTs.
    if filter_type == 'Rectangular':
        # Do what explained above

        transf = fftshift(fft(field))
        transf[abs(kspace) > filter_width/2] = 0

        filt_field = ifft(ifftshift(transf))
    else:
        # Do what explained above
        profile = np.exp(-(kspace / filter_width) ** 2 / 2)
        transf = fftshift(fft(field))
        transf = transf * profile

        filt_field = ifft(ifftshift(transf))

    intensity = np.sum(np.abs(transf).real ** 2) / dim ** 2

    with open('intensities.txt', 'a') as f:
        f.write(str(filter_width) + ' ' + str(intensity) + '\n')

    return filt_field

def create_pattern(field, slits_dist, screen, dist_2, wavelen, slit_width):
    """ This function profiles the filtered speckle field with a double slit and then propagates it on the final screen, creating the interference pattern to analyze
    Arguments:
        field: filtered speckle field on the plane where lies the double slit
        slits_dist: distance between the two slits in [cm]
        screen: coordinates of the points on the screen in [cm]
        dist_2: distance from the double slit and the screen on which interference is observed in [cm]
        wavelen: wavelength of the light in [cm]
        slit_width: width of each of the two slits in [cm]
    Returns:
        pattern: interference pattern generated by the speckle field given in input
    """


    dim = len(screen)

    pattern = np.zeros(dim, dtype = complex)

    index = np.arange(dim)
    slit_1 = np.logical_and(screen >= -slits_dist/2 - slit_width/2, screen <= -slits_dist/2 + slit_width/2)
    slit_2 = np.logical_and(screen >= slits_dist/2 - slit_width/2, screen <= slits_dist/2 + slit_width/2)
    slit_index = index[np.logical_or(slit_1, slit_2)]

    for i in slit_index:
        pattern += field[i] * np.exp(1j * 2 * np.pi * np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2) / wavelen) / np.sqrt(1 + (screen[i] - screen) ** 2 / dist_2 ** 2)

    # Return the interference pattern and the profile.
    return np.abs(pattern).real ** 2

# dist_2 = 1e4 # [cm]
# wavelen = 500 # [nm]
# slit_width = 1 # [mm]

def calc_extremal(vect, x_axis, tolerance):
    """ Calculate the extremal points of a function with tolerance to ignore fluctuations
    Arguments:
        vect: numpy array containing the y coordinates of the function graph
        x_axis: numpy array containing the x coordinates of the function graph
        tolerance: x interval over which the point must be an absolute maximum or minimum in order to be considered an extremal point
    Returns:
        (vect_max, vect_min): tuple with the indices of the local maxima and the local minima
    """
    vect_max = []
    vect_min = []

    dx = x_axis[1] - x_axis[0]

    i = 0
    while i < len(vect):
        if vect[i] == np.max(vect[np.logical_and(x_axis > x_axis[i] - tolerance/2, x_axis < x_axis[i] + tolerance/2)]):
            vect_max.append(i)
            i += round(tolerance/(2 * dx))
        elif vect[i] == np.min(vect[np.logical_and(x_axis > x_axis[i] - tolerance/2, x_axis < x_axis[i] + tolerance/2)]):
            vect_min.append(i)
            i += round(tolerance/(2 * dx))
        else:
            i += 1

    if vect_max[0] == 0: # If an extremal point is found at the edges of the vector, it's considered spurious.
        vect_max = vect_max[1:]
    if vect_max[-1] == len(vect) - 1:
        vect_max = vect_max[:-1]
    if vect_min[0] == 0:
        vect_min = vect_min[1:]
    if vect_min[-1] == len(vect) - 1:
        vect_min = vect_min[:-1]
            
    return vect_max, vect_min


def process_pattern(pattern_data, guess, A_1, B_1, dist_2, wavelen, slit_width, avg_intensity):
    """
    Calculate the upper and lower profile of a given interference pattern, use it to normalize the pattern itself, calculate the pattern visibility
    Arguments:
        pattern_data: pandas dataframe containing the interference pattern and the screen coordinates in [cm]
        guess: first guess for the visibility fit parameter
        A_1: first guess for the amplitude fit parameter
        B_1: first guess fot the horizontal dilation parameter
        dist_2: distance from the double slit to the screen in [cm]
        wavelen: wavelength of the light in [cm]
        slit_width: width of either of the two slits which produce the interference in [cm]
        avg_intensity: average intensity of the pattern 
    Returns:
        (patt_data_proc, patt_data_norm, vis): tuple containing: a pandas dataframe with the pattern, the screen and the two profiles; a pandas dataframe with 
        the normalized pattern and the screen; the numerical value of the visibility.
    """

    cut = 15 # [cm]
    slits_dist = pattern_data['slits_dist'][0]
    filter_width = pattern_data['filter_width'].to_numpy()[0]

    tolerance = 0.1 # [cm] (consider adding this as an input)

    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()

    dx = screen[1] - screen[0]

    pattern_cut = pattern[np.logical_and(screen >= -cut, screen <= cut)] # Cut away uninteresting part (the approximation used for the fit only works for small y)
    screen_cut = screen[np.logical_and(screen >= -cut, screen <= cut)]

    patt_max, patt_min = calc_extremal(pattern, screen, tolerance)

    def func_1(xx, sw, sd, wl, d, ai):
            # v, aa, bb = xx[0], xx[1], xx[2]
            # return np.mean(fit_up(screen[patt_max], *xx, sw, sd, wl, d, ai) * (fit_up(screen[patt_max], *xx, sw, sd, wl, d, ai) - pattern[patt_max]) ** 2) + np.mean(fit_down(screen[patt_min], *xx, sw, sd, wl, d, ai) * ((fit_down(screen[patt_min], *xx, sw, sd, wl, d, ai) - pattern[patt_min]) ** 2))
            return np.mean((fit_up(screen[patt_max], *xx, sw, sd, wl, d, ai) - pattern[patt_max]) ** 2) + np.mean(((fit_down(screen[patt_min], *xx, sw, sd, wl, d, ai) - pattern[patt_min]) ** 2))
    func_4 = lambda xxx: func_1(xxx, slit_width, slits_dist, wavelen, dist_2, avg_intensity)
    
    res = minimize(func_4, x0 = [guess, A_1, B_1])
    popt = res.x


    # popt_up, pcov_up = curve_fit(fit_up, screen_cut[patt_max], pattern_cut[patt_max], p0 = (guess, A_1))
    # popt_down, pcov_up = curve_fit(fit_down, screen_cut[patt_min], pattern_cut[patt_min], p0 = (guess, A_2))

    patt_up = fit_up(screen, *popt, slit_width, slits_dist, wavelen, dist_2, avg_intensity)
    patt_down = fit_down(screen, *popt, slit_width, slits_dist, wavelen, dist_2, avg_intensity)

    norm = fit_up(screen_cut, *popt, slit_width, slits_dist, wavelen, dist_2, avg_intensity)

    patt_norm = pattern_cut/norm # Normalized pattern

    patt_data_proc = pd.DataFrame({
        'screen': screen,
        'pattern': pattern,
        'prof_down': patt_down,
        'prof_up': patt_up
    })

    patt_data_norm = pd.DataFrame({
        'screen_cut': screen_cut,
        'patt_norm': patt_norm
    })

    # Calculation of visibility

    vis = (np.max(patt_norm) - np.min(patt_norm)) / (np.max(patt_norm) + np.min(patt_norm)) 
    # The normalized pattern should be a sinusoid, so the maximum and the minimum are well defined
    
    return patt_data_proc, patt_data_norm, round(vis, 3)

def pre_process(pattern_data, slit_width, wavelen, dist_2, options, guess, A_1, B_1, avg_intensity):
    """
    Generate the figures that appear in the pattern processing window
    Arguments: 
        pattern_data: pandas dataframe containing the interference pattern and the screen coordinates in [cm]
        slit_width: width of either of the two slits which produce the interference in [cm]
        wavelen: wavelength of the light in [cm]
        dist_2: distance from the double slit to the screen in [cm]
        options: a list of strings, either 'Extremal points' or 'Fit guess' or both, determining which of these are shown in the graph
        guess: first guess for the visibility fit parameter
        A_1: first guess for the amplitude fit parameter
        B_1: first guess fot the horizontal dilation parameter
        avg_intensity: average intensity of the pattern 
    Returns:
        (fig_data, fig_layout): tuple with the data and layout objects of the graph
    """

    slits_dist = pattern_data['slits_dist'][0]
    filter_width = pattern_data['filter_width'].to_numpy()[0]
    
    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()

    dx = screen[1] - screen[0]

    fig1 = px.line(pattern_data, x = 'screen', y = 'pattern', labels = {
        'screen': 'x [cm]',
        'pattern': 'Field intensity'
    })
    fig1.update_traces(line = dict(color = 'rgba(50,50,50,0.2)'))
    fig_data = fig1.data
    fig_layout = fig1.layout

    for i in options:
        if i == 'Extremal points':
            tolerance = 0.1 # [cm] (consider adding this as an input)
            patt_max, patt_min = calc_extremal(pattern, screen, tolerance) # compute local extrema of the pattern

            which = ['Maxima' for l in range(len(patt_max))] + ['Minima' for l in range(len(patt_min))] # remember which is a maximum and which a minimum

            maxmin_data = pd.DataFrame({ 
                'points': np.concatenate((screen[patt_max], screen[patt_min])),
                'maxes': np.concatenate((pattern[patt_max], pattern[patt_min])),
                'which': which
            })

            fig2 = px.scatter(maxmin_data, x = 'points', y = 'maxes', color = 'which') # plot

            fig_data += fig2.data

        elif i == 'Fit guess':
            # show how the fit function for the initial guess of the parameters looks like
            prof_up = fit_up(screen, guess, A_1, B_1, slit_width, slits_dist, wavelen, dist_2, avg_intensity) 
            prof_down = fit_down(screen, guess, A_1, B_1, slit_width, slits_dist, wavelen, dist_2, avg_intensity)

            guess_data = pd.DataFrame({
                'screen': screen,
                'Upper profile': prof_up,
                'Lower profile': prof_down
            })

            # plot
            fig3 = px.line(guess_data.melt(id_vars = 'screen', value_vars = ['Upper profile', 'Lower profile']), x = 'screen', y = 'value', line_group = 'variable', color = 'variable')
            # fig3 = px.line(guess_data, x = 'screen', y = 'prof_up')
            fig_data += fig3.data

        else: # Do the fast processing in order to be able to see the result
            pass
            _, _, screen_cut, patt_cut, norm = fast_process(pattern_data, slit_width, wavelen, dist_2, i, avg_intensity)
            fast_data = pd.DataFrame({
                'screen': screen_cut,
                # 'pattern': patt_cut,
                'profile': norm
            })
            fig4 = px.line(fast_data.melt(id_vars = 'screen', value_vars = ['profile']), x = 'screen', y = 'value', line_group = 'variable', color = 'variable')
            fig_data += fig4.data

    return fig_data, fig_layout

def fast_process(pattern_data, slit_width, wavelen, dist_2, method, avg_intensity):
    """ Calculate the visibility of a pattern automatically, more roughly, without using the fit
    Arguments: 
        pattern_data: pandas dataframe containing the interference pattern and the screen coordinates in [cm]
        slit_width: width of either of the two slits which produce the interference in [cm]
        wavelen: wavelength of the light in [cm]
        dist_2: distance from the double slit to the screen in [cm]
        method: whether to use a rought fit or a convex hull to compute the modulation
        avg_intensity: average intensity of the pattern 
    Returns:
        vis: the numerical value of the visibility
        pha: phase of the correlation function
        screen_cut: array of the screen point after cut
        pattern_cut: pattern array after cut
        norm: coumputed modulation of the interference pattern
    """
    
    cut = 15 # [cm]
    slits_dist = pattern_data['slits_dist'][0]
    filter_width = pattern_data['filter_width'].to_numpy()[0]

    tolerance = 0.1 # [cm] (consider adding this as an input)

    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()

    pattern_cut = pattern[np.logical_and(screen >= -cut, screen <= cut)] # Cut away uninteresting part (the approximation used for the fit only works for small y)
    screen_cut = screen[np.logical_and(screen >= -cut, screen <= cut)]

    dx = screen[1] - screen[0]

    if method == 'Rough fit':
        ## First method: fit

        patt_max, patt_min = calc_extremal(pattern, screen, tolerance)

        def func_2(xx, sw, sd, wl, d, ai): # function to minimize for the fit
            return np.mean((fit_up(screen[patt_max], *xx, sw, sd, wl, d, ai) - pattern[patt_max]) ** 2) + np.mean((fit_down(screen[patt_min], *xx, sw, sd, wl, d, ai) - pattern[patt_min]) ** 2)
        func_3 = lambda xxx: func_2(xxx, slit_width, slits_dist, wavelen, dist_2, avg_intensity)

        res = minimize(func_3, x0 = [0.5, 1.0, 1.0])
        popt = res.x

        # popt_up, pcov_up = curve_fit(fit_up, screen_cut[patt_max], pattern_cut[patt_max], p0 = (guess, A_1))
        # popt_down, pcov_up = curve_fit(fit_down, screen_cut[patt_min], pattern_cut[patt_min], p0 = (guess, A_2))

        # patt_up = fit_up(screen, *popt)
        # patt_down = fit_down(screen, *popt)

        norm = fit_up(screen_cut, *popt, slit_width, slits_dist, wavelen, dist_2, avg_intensity)

    elif method == 'Convex hull':
        ## Second method: calculate the modulation as the concave hull of the data
        index = np.arange(len(pattern_cut))
        norm = np.zeros_like(pattern_cut)
        i = 0
        while i < len(pattern_cut) - 1: # computation of the convex hull
            temp1 = pattern_cut[index > i]
            temp2 = screen_cut[index > i]
            temp3 = index[index > i]
            coeff = (temp1 - pattern_cut[i]) / (temp2 - screen_cut[i])
            j = temp3[coeff == np.max(coeff)][0]
            norm[i:j + 1] = pattern_cut[i] + np.max(coeff) * (screen_cut[i:j + 1] - screen_cut[i])
            i = j

    patt_norm = pattern_cut / norm # Normalized pattern

    # Calculation of visibility

    vis = (np.max(patt_norm) - np.min(patt_norm)) / (np.max(patt_norm) + np.min(patt_norm)) 
    # The normalized pattern should be a sinusoid, so the maximum and the minimum are well defined

    pha = 0 # Phase of the correlation function
    center = round(len(screen_cut) / 2) # Center of the screen

    if center + round(wavelen * dist_2 / (slits_dist * dx)) >= len(patt_norm): # Necessary when the slits are so close that the pattern hardly oscillates
        pha = 1
    elif patt_norm[center] > patt_norm[center + round(wavelen * dist_2 / (slits_dist * dx))]: # In this case the center is a maximum
        pha = 1
    else: # otherwise it's a minimum
        pha = -1
    
    return round(vis, 3), pha, screen_cut, pattern_cut, norm

def FWHM(vect, x_axis):
    """ Calculate the FWHM of a peaked function
    Arguments:
        vect: numpy array containing the y coordinates of the function graph
        x_axis: numpy array containing the x coordinates of the function graph
    Returns:
        FWHM: width of the function peak calculated as the full width at half maximum
    """
    FW = x_axis[vect >= 0.5]
    if FW.size:
        FWHM = FW[-1] - FW[0]
    else:
        FWHM = 0

    return FWHM