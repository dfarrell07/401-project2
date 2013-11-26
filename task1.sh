#!/usr/bin/env bash
# Author: Daniel Farrell
# Public Domain
# Runs task1 of the spec using Go-Back-N and graphs the results

TIMEFORMAT=%R

mss=500
p=.05
rand_size=1000000
infile=infile
outfile=outfile
shost=152.14.104.45
sport=7735
results=data_gbn1
repeats=20
n_ceiling=1024

# Build file to transfer
echo SCRIPT: Building file to transfer
echo "$(dd if=/dev/urandom bs=1 count=$rand_size)" > $infile

# Add columns to result file
echo "n,avg_delay" > $results

# Update server's code
echo SCRIPT: Updating remote server code
scp server.py adminuser@$shost:/home/adminuser/p2/

n=1
repeats_done=0
delay_sum=0
while [ $n -le $n_ceiling ]
do
    while [ $repeats_done -lt $repeats ]
    do
        # Kill any running server process
        ssh adminuser@$shost "pkill python"

        # Start server
        echo SCRIPT: Starting remote server with sport:$sport outfile:$outfile p:$p n:$n
        ssh adminuser@$shost "python /home/adminuser/p2/server.py $sport $outfile $p $n > slog &" &

        sleep 2

        # Start client
        echo SCRIPT: Starting client with host:$shost port:$sport n:$n mss:$mss
        delay=$(time (python client.py $shost $sport $infile $n $mss >/dev/null 2>&1) 2>&1)

        # Report run result
        echo "SCRIPT: (n,delay) is ($n,$delay)"

        # Update vars
        delay_sum=$(echo "scale=3;$delay_sum+$delay" | bc)
        let repeats_done=$repeats_done+1
    done
    # Get average delay
    avg_delay=$(echo "scale=3;$delay_sum/$repeats_done" | bc)

    echo "SCRIPT: Average (n,delay_sum) : ($n,$delay_sum) is $avg_delay"

    # Write results to file
    echo "$n,$avg_delay" >> $results

    # Update vars
    let n=$n*2
    repeats_done=0
    delay_sum=0
done

# Kill any running server process
ssh adminuser@$shost "pkill python"

# Build R script that graphs results
echo "gbnd1 <- read.table(\"./data_gbn1\", header=T, sep=\",\")
max_delay <- max(gbnd1\$avg_delay)
plot(x=gbnd1\$n, y=gbnd1\$avg_delay, ylim=c(min(gbnd1\$avg_delay),1.1*max(gbnd1\$avg_delay)), col='blue', type=\"o\", main='Task 1 - Go-Back-N ARQ', ylab='Delay (Seconds)', xlab='Window Size N')
abline(lm(gbnd1\$avg_delay~gbnd1\$n))
box()
" > Rscript_gbn1

# Execute R script
R CMD BATCH ./Rscript_gbn1
