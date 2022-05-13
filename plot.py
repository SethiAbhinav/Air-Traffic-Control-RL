import numpy as np
import matplotlib.pyplot as plt

def displayScores():
    for i in [25,50,75,100,125]:
        loss = np.load(f"results/episode_{i}score.npy")
        epochs = np.linspace(0, len(loss), num=len(loss))
        plt.figure()
        plt.title('Scores Over Time')
        plt.xlabel("Epochs")
        plt.ylabel('Score')
        plt.plot(epochs, loss)
        # plt.show()
        plt.savefig(f"result_figs/episode_{i}score.png")

        cumsum = np.cumsum(loss)
        avg = np.divide(cumsum, epochs+1)
        plt.figure()
        plt.title('Average Scores Over Time')
        plt.xlabel("Epochs")
        plt.ylabel('Average Score')
        plt.plot(epochs, avg)
        # plt.show()
        plt.savefig(f"result_figs/episode_{i}average_score.png")

displayScores()
