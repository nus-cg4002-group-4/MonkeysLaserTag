import csv

def write_to_csv(packets: [], file_count):

    # field names 
    fields_gyro = ['gx', 'gy', 'gz'] 
    fields_accel = ['ax', 'ay', 'az']
    combined_fields = ['ax', 'ay', 'az','gx', 'gy', 'gz', 'flex']

    # with open("gyro_data_" + str(file_count) + ".csv", 'w', newline='') as g_file: 
    #     gyro_writer = csv.DictWriter(g_file, fieldnames = fields_gyro)

    #     gyro_writer.writeheader() 

    #     for i in range(len(packets)):
    #         gyro_writer.writerow({'gx': packets[i].gx, 'gy': packets[i].gy, 'gz': packets[i].gz})

    # with open("accel_data_" + str(file_count) + ".csv", 'w', newline ='') as a_file:
    #     a_writer = csv.DictWriter(a_file, fieldnames=fields_accel)
    #     a_writer.writeheader()
    #     for i in range(len(packets)):
    #         a_writer.writerow({'ax': packets[i].ax, 'ay': packets[i].ay, 'az': packets[i].az})

    with open("combined_data_" + str(file_count) + ".csv", 'w', newline ='') as combined_file:
        a_writer = csv.DictWriter(combined_file, fieldnames=combined_fields)
        a_writer.writeheader()
        for i in range(len(packets)):
            a_writer.writerow({'ax': packets[i].ax, 'ay': packets[i].ay, 'az': packets[i].az, 'gx': packets[i].gx, 'gy': packets[i].gy, 'gz': packets[i].gz, 'flex': packets[i].flex})
    

def write_to_csv_test(packets: []):

    # field names 
    fields_gyro = ['gx', 'gy', 'gz'] 
    fields_accel = ['ax', 'ay', 'az']

    with open('gyro_data.csv', 'w', newline='') as g_file: 
        gyro_writer = csv.DictWriter(g_file, fieldnames = fields_gyro)

        gyro_writer.writeheader() 

        for i in range(len(packets)):
            gyro_writer.writerow({'gx': packets[i][0], 'gy': packets[i][1], 'gz': packets[i][2]})

    with open('accel_data.csv', 'w', newline ='') as a_file:
        a_writer = csv.DictWriter(a_file, fieldnames=fields_accel)
        a_writer.writeheader()

        for i in range(len(packets)):
            a_writer.writerow({'ax': packets[i][0], 'ay': packets[i][1], 'az': packets[i][2]})

if __name__ == "__main__":
    packets = [
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
        (1,1,1),
    ]

    for i in range(len(packets)):
        print(str(i) + ":" + str(packets[i][0]))

    write_to_csv_test(packets)
