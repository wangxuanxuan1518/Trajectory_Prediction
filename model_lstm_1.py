import tensorflow as tf

class lstm_model(tf.keras.Model):

    def __init__(self,enc_units, batch_sz):

        super(lstm_model, self).__init__()
        self.batch_sz = batch_sz
        self.enc_units = enc_units
        self.lstm = tf.keras.layers.LSTM(self.enc_units,
                                        return_sequences=True,
                                        return_state=True,
                                        recurrent_initializer='glorot_uniform')
        self.fc = tf.keras.layers.Dense(2, activation='elu')
        self.dropout = tf.keras.layers.Dropout(0.2)
        self.batchnormalization = tf.keras.layers.BatchNormalization()
        self.embedding = tf.keras.layers.Dense(32, activation='elu')

    def call(self, x, hidden, cell,mode):
        
        input_embedding = self.embedding(x)

        if mode == 'train':
            input_x = self.dropout(input_embedding)
        else:
            input_x = input_embedding

        output, state_h, state_c = self.lstm(input_x, initial_state = [hidden,cell])
        output_1 = self.batchnormalization(output)
        results = self.fc(output_1)

        return results,state_h,state_c

    def initialize_hidden_state(self):
        return tf.zeros((self.batch_sz, self.enc_units))

    def initialize_cell_state(self):
        return tf.zeros((self.batch_sz, self.enc_units))