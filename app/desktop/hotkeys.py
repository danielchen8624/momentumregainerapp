from pynput import keyboard

COMBINATIONS = [
    {keyboard.Key.shift, keyboard.KeyCode(char='a')}, #combo 1
    {keyboard.Key.shift, keyboard.KeyCode(char='A')} #combo 2

]
current = set()

def startListener(execute_callback):

    def on_press(key):
        if any([key in COMBO for COMBO in COMBINATIONS]):
            current.add(key)
            if any(all(k in current for k in COMBO) for COMBO in COMBINATIONS): # Check if any combination is complete. all (k in current for k in COMBO) means return true if each k in combo has a corresponding k in current
                 execute_callback()

    def on_release(key): 
        if any([key in COMBO for COMBO in COMBINATIONS]): #if you release a key and it is in a combo, remove key from current
            current.discard(key) #discard does not raise an error if the key is not found, safer than remove

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        