"""proc_video.py: Provides a few methods to extract properties from videos"""

import numpy as np
import cv2
import sys
import re

def get_video_properties(vid_file, should_write=False):
    """Return all of the properties of the video."""
    def_num_bins = 3
    
    mean = get_mean(vid_file)
    tempo = get_tempo(vid_file)
    h_bins, s_bins, v_bins = get_color_bins(vid_file, def_num_bins)

    if should_write:
        mean_fname = re.sub('\..*', '_mean.jpg', vid_file)
        mean_fname = re.sub('res/', 'out/', mean_fname)
        cv2.imwrite(mean_fname, mean)
        
        fname = re.sub('\..*', '.txt', vid_file)
        fname = re.sub('res/', 'out/', fname)
        f = open(fname, 'w')
        f.write('Mean: ' + mean_fname + '\n')
        f.write('Tempo: ' + `tempo` + '\n')
        
        f.write('Hue weights: \n')
        for i in range(def_num_bins):
            f.write('\t[' + `i*179/def_num_bins` + ', ' + `(i+1)*179/def_num_bins` + ']: ')
            f.write(`h_bins[i]` + '\n')
            
        f.write('Saturation weights: \n')
        for i in range(def_num_bins):
            f.write('\t[' + `i*255/def_num_bins` + ', ' + `(i+1)*255/def_num_bins` + ']: ')
            f.write(`s_bins[i]` + '\n')
            
        f.write('Value weights: \n')
        for i in range(def_num_bins):
            f.write('\t[' + `i*255/def_num_bins` + ', ' + `(i+1)*255/def_num_bins` + ']: ')
            f.write(`v_bins[i]` + '\n')

        f.close()
        
    return mean, tempo, h_bins, s_bins, v_bins

def get_mean(vid_file):
    """Return the average frame across the whole video."""
    vid = cv2.VideoCapture(vid_file)
    num_frames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
    
    retval, im = vid.read()
    mean = np.zeros((len(im), len(im[0]), 3))
    num = 1.0
    cv2.accumulate(im,mean)
    frame = 0
    
    while retval:
        frame += 1
        sys.stdout.write('\rgetting mean: ' + `(frame * 100) / int(num_frames)` + '%')
        sys.stdout.flush()

        cv2.accumulate(im, mean)
        num += 1
        retval, im = vid.read()

    print '\ndone getting mean'
        
    mean = mean / num
    mean = mean.astype("uint8")
    vid.release()

    return mean

def get_tempo(vid_file):
    """Return the tempo property which is dependent on difference frames."""
    vid = cv2.VideoCapture(vid_file)
    num_frames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
    width = vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
    height = vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    num_pixels = width * height * 3

    retval, im1 = vid.read()
    retval, im2 = vid.read()

    total = np.zeros((height, width, 3))
    cv2.accumulate(im1, total)
    frame = 0
    
    while retval:
        frame += 1
        sys.stdout.write('\rgetting tempo: ' + `(frame * 100) / int(num_frames)` + '%')
        sys.stdout.flush()
        cv2.accumulate(cv2.subtract(im2,im1), total)
        im1 = im2
        retval, im2 = vid.read()

    print '\ndone getting tempo'
    vid.release()
    tempo = np.sum(total) / (num_pixels * num_frames * 255.0)
    
    return tempo

def get_color_bins(vid_file, num_bins, should_write=False):
    """Get the top three colors (that are 'binned') in the video."""
    vid = cv2.VideoCapture(vid_file)
    num_frames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
    width = vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
    height = vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)
    fourcc = vid.get(cv2.cv.CV_CAP_PROP_FOURCC)
    
    hue_bins = np.zeros(num_bins)
    sat_bins = np.zeros(num_bins)
    val_bins = np.zeros(num_bins)
    
    if should_write:
        writers = {}
        basename = re.sub('?.*/', '', vid_file)
        for i in range(num_bins):
            writers[i] = cv2.VideoWriter('./out/' + 'basename' + '(' + `i` + ').mov', cv2.cv.FOURCC('m','p','4','v'), fps, (int(width), int(height)))

    retval, im = vid.read()
    frame = 0
        
    while retval:
        frame += 1
        sys.stdout.write("\rgetting color bins: " + `(frame * 100) / int(num_frames)` + "%")
        sys.stdout.flush()
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        
        for i in range(num_bins):
            h_low  = (i * 179) / num_bins
            h_high = ((i + 1) * 179) / num_bins
            lower = np.array([h_low, 0, 0])
            upper = np.array([h_high, 255, 255])
            mask  = cv2.inRange(hsv, lower, upper)
            hue_bins[i] += np.sum(mask) / (width * height * 255)

            s_low  = (i * 255) / num_bins
            s_high = ((i + 1) * 255) / num_bins
            lower = np.array([0, s_low, 0])
            upper = np.array([179, s_high, 255])
            mask  = cv2.inRange(hsv, lower, upper)
            sat_bins[i] += np.sum(mask) / (width * height * 255)

            v_low  = (i * 255) / num_bins
            v_high = ((i + 1) * 255) / num_bins
            lower = np.array([0, 0, v_low])
            upper = np.array([179, 255, v_high])
            mask  = cv2.inRange(hsv, lower, upper)
            val_bins[i] += np.sum(mask) / (width * height * 255)

            if should_write:
                res   = cv2.bitwise_and(im, im, mask=mask)
                writers[i].write(res)

        retval, im = vid.read()

    print '\ndone getting colors'
    
    if should_write:
        for i in range(num_bins):
            writers[i].release()

    hue_bins = hue_bins / frame
    sat_bins = sat_bins / frame
    val_bins = val_bins / frame
            
    return hue_bins, sat_bins, val_bins

def play_diff(vid_file):
    """For fun, play the difference frames as a video."""
    vid = cv2.VideoCapture(vid_file)

    retval, im1 = vid.read()
    retval, im2 = vid.read()

    cv2.namedWindow('image', cv2.cv.CV_WINDOW_NORMAL)
    
    while retval:
        cv2.imshow('image', cv2.subtract(im2,im1))
        cv2.waitKey(1)
        im1 = im2
        retval, im2 = vid.read()

    vid.release()
    cv2.destroyWindow("image")
    cv2.waitKey(1)
