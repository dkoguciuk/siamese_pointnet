#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@author: Daniel Koguciuk <daniel.koguciuk@gmail.com>
@note: Created on 24.12.2017
'''

import os
import sys
import shutil
import argparse
import numpy as np
import tensorflow as tf
import train_with_hparam
import siamese_pointnet.defines as df
import siamese_pointnet.modelnet_data as modelnet
from siamese_pointnet.classifiers import MLPClassifier
from siamese_pointnet.model import OrderMattersModel

CLOUD_SIZE = 32
CLASSIFIER_MODEL_LOAD = False

def train_classification(name, batch_size, epochs, learning_rate, device,
                         read_block_units, process_block_steps,
                         classifier_layers = [1024, 512, 256, 128, 40]):
    """
    Train siamese pointnet classificator with synthetic data.
    """

    # Reset
    tf.reset_default_graph()

    # Generate data if needed
    data_gen = modelnet.SyntheticData(pointcloud_size=CLOUD_SIZE)

    ##################################################################################################
    ################################## FEATURES EXTRACTION MODEL #####################################
    ##################################################################################################

    with tf.variable_scope("end-to-end"):
        with tf.device(device):
            features_model = OrderMattersModel(train=False,
                                               batch_size = batch_size,
                                               pointcloud_size = CLOUD_SIZE,
                                               read_block_units = read_block_units,
                                               process_block_steps=process_block_steps)
            features_vars = tf.get_collection(key=tf.GraphKeys.TRAINABLE_VARIABLES,
                                                scope="end-to-end")
            features_model_saver = tf.train.Saver(features_vars)

    ##################################################################################################
    ##################################### CLASSIFICATION MODEL #######################################
    ##################################################################################################

    with tf.device(device):
        classifier_model = MLPClassifier(classifier_layers, batch_size, learning_rate)
        if CLASSIFIER_MODEL_LOAD:
            classifier_vars = tf.get_collection(key=tf.GraphKeys.TRAINABLE_VARIABLES,
                                                scope=classifier_model.MODEL_NAME)
            classifier_model_saver = tf.train.Saver(classifier_vars)

    ##################################################################################################
    ############################################ SESSION #############################################
    ##################################################################################################

    config = tf.ConfigProto(allow_soft_placement=True)
    config.gpu_options.allow_growth=True
    with tf.Session(config=config) as sess:
#     with tf.Session() as sess:

        ##############################################################################################
        ######################################## INIT VARIABLES ######################################
        ##############################################################################################

        sess.run(tf.global_variables_initializer())
        features_model_saver.restore(sess, tf.train.latest_checkpoint('models_17'))
        if CLASSIFIER_MODEL_LOAD:
            classifier_model_saver.restore(sess, tf.train.latest_checkpoint('models_classifier'))

        ##############################################################################################
        ######################################## SUMMARY WRITER ######################################
        ##############################################################################################

        log_model_dir = os.path.join(df.LOGS_DIR, classifier_model.get_model_name())
        writer = tf.summary.FileWriter(os.path.join(log_model_dir, name))
#         writer.add_graph(sess.graph)
        
        ##############################################################################################
        ##################################### EPOCH TRAINING LOOP ####################################
        ##############################################################################################
        
        global_batch_idx = 1
        #summary_skip_batch = 10
        checkpoint_skip_epochs = 25
        for epoch in range(epochs):

            ##########################################################################################
            ##################################### BATCH TRAINING LOOP ################################
            ##########################################################################################

            #epoch_batch_idx = 1
            for clouds, labels in data_gen.generate_random_batch(train = True,
                                                                 batch_size = batch_size,
                                                                 shuffle_points=True,
                                                                 jitter_points=True,
                                                                 rotate_pointclouds=False):

                ##################################################################################################
                ######################################### GET EMBEDDING ##########################################
                ##################################################################################################

                # count embeddings
                embedding_input = np.stack([clouds], axis=1)
                embeddings = sess.run(features_model.get_embeddings(), feed_dict={features_model.placeholder_embdg: embedding_input})

                ##################################################################################################
                ############################################# TRAIN ##############################################
                ##################################################################################################

                # run optimizer
                new_labels = sess.run(tf.one_hot(labels, 40))
                _, loss, summary_train = sess.run([classifier_model.get_optimizer(),
                                                   classifier_model.get_loss_function(),
                                                   classifier_model.get_summary()],
                                                   feed_dict={classifier_model.placeholder_embed: embeddings,
                                                              classifier_model.placeholder_label: new_labels})
 
                global_batch_idx += 1
                #epoch_batch_idx += 1
                
            ##################################################################################################
            ################################### CLASSIFICATION ACCURACY ######################################
            ##################################################################################################
            
            #if global_batch_idx % summary_skip_batch == 0:
                
            # Get test embeddings
            hit = 0.
            all = 0.
            for clouds, labels in data_gen.generate_random_batch(False, 16):# 400 test examples / 16 clouds = 25 batches
            
                # padding
                clouds_padding = np.zeros((batch_size - 16, 32, 3), dtype=np.float)
                clouds_padded = np.concatenate((clouds, clouds_padding), axis=0)
                labels_padding = np.zeros((batch_size - 16), dtype=np.int)
                labels_padded = np.concatenate((labels, labels_padding), axis=0)
                
                # count embeddings
                embedding_input = np.stack([clouds_padded], axis=1)
                embeddings = sess.run(features_model.get_embeddings(),
                                           feed_dict={features_model.placeholder_embdg: embedding_input})
                
                # One hot
                labels_padded_one_hot = sess.run(tf.one_hot(labels_padded, 40))
                pred = sess.run(classifier_model.get_classification_prediction(),
                                feed_dict={classifier_model.placeholder_embed: embeddings,
                                           classifier_model.placeholder_label: labels_padded_one_hot})
                
                # accuracy 
                predictions = np.argmax(pred, axis=1)
                predictions = predictions[:len(labels)]
                hit = hit + sum(predictions == labels)
                all = all + len(labels)
            
            ##################################################################################################
            ############################################# SUMMARIES ##########################################
            ##################################################################################################
              
            summary_test = tf.Summary()
            summary_test.value.add(tag="%stest_classification_accuracy" % "", simple_value= (hit / all))
            writer.add_summary(summary_test, global_batch_idx)
            writer.add_summary(summary_train, global_batch_idx)
            print "Epoch: %06d batch: %03d loss: %06f test_accuracy: %06f" % (epoch + 1, global_batch_idx, loss, (hit / all))

            ##################################################################################################
            ################################## SAVE CLASSIFICATION MODEL #####################################
            ##################################################################################################

            if (epoch+1) % checkpoint_skip_epochs == 0:

                # Save model
                save_path = classifier_model.save_model(sess, name)
                print "Model saved in file: %s" % save_path

def main(argv):

    # Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", help="Name of the run", type=str, required=True)
    parser.add_argument("-b", "--batch_size", help="The size of a batch", type=int, required=False, default=64)
    parser.add_argument("-e", "--epochs", help="Number of epochs of training", type=int, required=False, default=25)
    parser.add_argument("-l", "--learning_rate", help="Learning rate value", type=float, required=True)
    parser.add_argument("-r", "--read_block_units", help="Read block units", type=int, required=False, default=256)
    parser.add_argument("-p", "--process_block_steps", help="Process block steps", type=int, required=False, default=4)
    parser.add_argument("-d", "--device", help="Which device to use (i.e. /device:GPU:0)", type=str, required=False, default="/device:GPU:0")
    args = vars(parser.parse_args())

    # train
    train_classification(args["name"], batch_size=args["batch_size"], epochs=args["epochs"],
                         learning_rate=args["learning_rate"], device=args["device"],
                         read_block_units=[args["read_block_units"]], process_block_steps=args["process_block_steps"])

    # Print all settings at the end of learning
    print "Classification model:"
    print "name                 = ", args["name"]
    print "batch_size           = ", args["batch_size"]
    print "epochs               = ", args["epochs"]
    print "learning rate        = ", args["learning_rate"]
    print "read_block_units     = ", args["read_block_units"]
    print "process_block_steps  = ", args["process_block_steps"]
    
    # Send end of training e-mail 
    email_sender = train_with_hparam.EmailSender()
    email_sender.send(["daniel.koguciuk@gmail.com"], "Work Done!", "")


if __name__ == "__main__":
    main(sys.argv[1:])