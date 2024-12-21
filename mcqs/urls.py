
from django.contrib import admin
from django.urls import path, include
from mcqs.views import cus_mcq,test,submit_quiz,save_answer,continue_test,submitted_active,cont_last_sess,analysis_by_difficulty,accuracy_vs_tests,analysis_view_sub_acc,performance_radar_view,difficulty_vs_time_view,type_vs_time,diff_corr_incorr,type_corr_incorr,rev_test_home,test_review,tea,toggle_bookmark,bookmarks_home,delete_bookmark,qod
    

urlpatterns = [
    path('', cus_mcq,  name='mcq' ),
    
    path('test/', test,  name='test' ),
    
    path('submit_quiz/', submit_quiz, name='submit_quiz'),
    path('save-answer/', save_answer, name='save_ans'),
    path('restest/<test_id>', continue_test, name='cont'),
    path('submitted_active/', submitted_active, name='submitted_active'),
    path('cont_last_sess/', cont_last_sess , name='cont_last_sess'),
    path('ana/', analysis_by_difficulty , name='analysis_by_difficulty'),
    path('acc_test/', accuracy_vs_tests , name='accuracy_vs_tests'),
    path('sub_acc/', analysis_view_sub_acc , name='analysis_view_sub_acc'),
    path('radar/', performance_radar_view , name='performance_radar_view'),
    path('diff_vs_time/', difficulty_vs_time_view , name='difficulty_vs_time_view'),
    path('type_vs_time/', type_vs_time , name='type_vs_time'),
    path('diff_corr_incorr/', diff_corr_incorr , name='diff_corr_incorr'),
    path('type_corr_incorr/', type_corr_incorr , name='type_corr_incorr'),
    path('rev_test_home/', rev_test_home , name='rev_test_home'),
    path('rev_test_home/rev_test/', test_review, name='test_review'),
    path('tea/', tea, name='tea'),
    path('toggle-bookmark/', toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', bookmarks_home, name='bookmarks'),
    path('delete-bookmark/<str:bkmk_id>/', delete_bookmark, name='delete_bookmark'),
    path('qod/', qod, name='qod'),
]                      

