#!/usr/bin/env bash
# Author: Daniel Farrell
# Public Domain
# Runs task3 of the spec using Go-Back-N and graphs the results

TIMEFORMAT=%R

mss=500
n=64
rand_size=1000000
infile=infile
outfile=outfile
shost=152.14.104.45
sport=7735
results=data_gbn3
repeats=20
p_step=.01
p_do_steps=10

# Build file to transfer
echo SCRIPT: Building file to transfer
echo "$(dd if=/dev/urandom bs=1 count=$rand_size)" > $infile

# Add columns to result file
echo "p,avg_delay" > $results

# Update server's code
echo SCRIPT: Updating remote server code
scp server.py adminuser@$shost:/home/adminuser/p2/

p=.01
repeats_done=0
delay_sum=0
# Using this vs float conditionals in bash
p_steps_done=0 
while [ $p_steps_done -lt $p_do_steps ]
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
        echo "SCRIPT: (p,delay) is ($p,$delay)"

        # Update vars
        delay_sum=$(echo "scale=3;$delay_sum+$delay" | bc)
        let repeats_done=$repeats_done+1
    done
    # Get average delay
    avg_delay=$(echo "scale=3;$delay_sum/$repeats_done" | bc)

    echo "SCRIPT: Average (p,delay_sum) : ($p,$delay_sum) is $avg_delay"

    # Write results to file
    echo "$p,$avg_delay" >> $results

    # Update vars
    p=$(echo "scale=4;$p+$p_step" | bc)
    repeats_done=0
    let p_steps_done=$p_steps_done+1
    delay_sum=0
done

# Kill any running server process
ssh adminuser@$shost "pkill python"

# Build R script that graphs results
echo "gbnd3 <- read.table(\"./data_gbn3\", header=T, sep=\",\")
max_delay <- max(gbnd3\$avg_delay)
plot(x=gbnd3\$p, y=gbnd3\$avg_delay, ylim=c(min(gbnd3\$avg_delay),1.1*max(gbnd3\$avg_delay)), col='blue', type=\"o\", main='Task 3 - Go-Back-N ARQ', ylab='Delay (Seconds)', xlab='Packet Loss Probability P')
abline(lm(gbnd3\$avg_delay~gbnd3\$p))
box()
" > Rscript_gbn3

# Execute R script
R CMD BATCH ./Rscript_gbn3
