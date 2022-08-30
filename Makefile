g=g++
do:
	$(g) Cipherfour.cpp -o Cipherfour -O2
	./Cipherfour
clean:
	rm -f Cipherfour