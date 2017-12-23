#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@author: Daniel Koguciuk <daniel.koguciuk@gmail.com>
@note: Created on 24.12.2017
'''

import sys
import argparse
import tensorflow as tf
from siamese_pointnet.model import Model
import siamese_pointnet.data_generator as gen

def train_pointnet():
    """
    Train siamese pointnet.
    """
    layers_sizes = [2048, 1024, 512, 256, 128]
    batch_size = 32
    initialization_method = "xavier"
    hidden_activation = "relu"
    output_activation = "relu"
    margin = 0.2
    learning_rate = 0.001
    num_epochs = 100
    
    # Define model
    model = Model(layers_sizes, batch_size, initialization_method, hidden_activation, output_activation, margin)
    
    # Define Training procedure
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(model.loss)
 
    # merge all summaries
    tf.summary.merge_all()
    
    # Init all vars
    init = tf.initialize_all_variables()
    
    # Session
    with tf.Session() as sess:
        
        # Run the initialization
        sess.run(init)
        
        # Do the training loop
        for _ in range(num_epochs):
        
            # Loop for all batches
            data = None
            labels = None
            for (cloud_a, cloud_p, cloud_n) in gen.generate_next_data(data, labels, batch_size):

                # Run optimizer
                _, _ = sess.run([optimizer, model.loss], feed_dict={model.input_a: cloud_a,
                                                                       model.input_p: cloud_p,
                                                                       model.input_n: cloud_n})
            
            

def main(argv):

    # Parser
    parser = argparse.ArgumentParser()
#    parser.add_argument("-i", "--input", help="bla bla bla", type=str, required=True)
    args = vars(parser.parse_args())

    # train
    train_pointnet()

if __name__ == "__main__":
    main(sys.argv[1:])
 