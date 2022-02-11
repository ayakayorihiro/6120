# Lesson 2 Tasks
I wrote a small program in python that transforms a given Bril program by swapping between addition and subtraction, and multiplication and division. So, any program that has an integer arithmetic operation that is outputted from the program will now have a different arithmetic operation instead. To test my small program, I wrote 4 toy tests in Bril each using addition, subtraction, multiplication, and division opearators, and one of those programs uses two different kinds of arithmetic (`div.bril` has both division and multiplication). I tested by first checking the json output from my program, which I verified contained the relevant transformations, and then I tested by running each test program in the original version and in the transformed version.